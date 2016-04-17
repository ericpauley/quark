
express = require('express')

var app = express()
var http = require('http').Server(app)

var redis = require("redis"),
master = redis.createClient();
receiver = redis.createClient();

gdatas = {}
grec = false
receivers = {}

var io = require('socket.io')(http);

receiver.on("ready", function(){
  receiver.psubscribe("*.running")
  receiver.psubscribe("*.graphs")
  receiver.psubscribe("*.logs")
});

receiver.on("pmessage", function(pattern, channel, message){
  parts = channel.split(".")
  if(parts[1] == "running"){
    io.to(parts[0]).emit("running",message)
  }else if(parts[1] == "graphs"){
    gdata = JSON.parse(message)
    gdatas[parts[0]] = gdata
    if(receivers.hasOwnProperty(parts[0])){
      receivers[parts[0]].disconnect()
    }
    io.to(parts[0]).emit("gdata", gdata)
    if(grec){
      grec.quit()
    }
    grec = redis.createClient()
    for(var i = 0;i<gdata.length;i++){
      console.log(i)
      var gnum = i
      var graph = gdata[i]
      console.log(graph)
      for(var j = 0;j<graph.channels.length;j++){
        var gseries = graph.channels[j]
        console.log(gseries)
        grec.psubscribe(gseries)
        grec.on("pmessage", function(pattern, channel, message){
          data = JSON.parse(message)
          console.log(data)
          console.log(pattern, gseries)
          if(pattern == gseries){
            io.to(parts[0]).emit("graph", {graph:gnum, series:channel, t:data.t, val:data.val})
          }
        })
      }
    }
  }else if(parts[1] == "logs"){
    io.to(parts[0]).emit("logs", JSON.parse(message))
  }
})

app.use(express.static('html'))

io.on('connection', function(socket){
  var page = ""
  master.smembers("sketches", function(err, sketches){
    socket.emit("sketches", sketches)
  })
  socket.on('page', function(message){
    page = message.name
    socket.join(page)
    master.sadd("sketches",page, function(){
      master.smembers("sketches", function(err, sketches){
        socket.emit("sketches", sketches)
      })
    })
    master.hgetall(page+".devices", function(err,data){
      socket.emit("devices", data)
    })
    master.get(page+".code", function(err,code){
      console.log(page+".code",code)
      if(code != null){
        socket.emit('page', {code:code})
      }else{
        socket.emit('page', {code:""})
      }
    })
    master.get(page+".running",function(err, running){
      socket.emit("running", running)
      if(running && gdatas[page]){
        socket.emit("gdata", gdatas[page])
      }
    })
    socket.on("associate", function(message){
      master.hget("associations", message.id,function(err, val){
        if(val){
          sketch = val.split(".")[0]
          device = val.split(".")[1]
          master.hdel(sketch+".devices", device)
        }
        master.hset("associations", message.id, page+"."+message.name)
        master.hset(page+".devices", message.name, message.id, function(){
          console.log("associated!")
          master.hgetall(page+".devices", function(err,data){
            socket.emit("devices", data)
          })
        })
      })
    })
  })
  socket.on('save', function(message){
    master.set(page+".code",message.code)
    socket.broadcast.to(page).emit('page', {code:message.code})
  })
  socket.on('save_run', function(message){
    master.set(socket.page+".code",message.code,function(){
      master.publish("control", JSON.stringify({cmd:"start",name:page}))
    })
  })
  socket.on('stop', function(message){
    if(grec){
      grec.quit()
    }
    master.publish("control", JSON.stringify({cmd:"stop",name:page}))
  })
});

app.get('/', function(req, res){
  res.send('<h1>Hello world</h1>')
});

app.get('/:page', function(req, res){
  res.sendFile("html/index.html", {root:__dirname});
})

http.listen(3000, function(){
  console.log('listening on *:3000')
});
