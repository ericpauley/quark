express = require('express')

var app = express()
var http = require('http').Server(app)
app.use(express.static('html'))

var redis = require("redis"),
master = redis.createClient();
receiver = redis.createClient();

gdatas = {}
receivers = {}

var io = require('socket.io')(http);

receiver.on("ready", function(){
  receiver.psubscribe("*.running")
});

receiver.on("pmessage", function(pattern, channel, message){
  parts = channel.split(".")
  if(parts[1] == "running"){
    io.to(parts[0]).emit("running",message)
  }else if(parts[1] == "graphs"){
    gdata = json.parse(message)
    gdatas[parts[0]] = gdata
    if(receivers.hasOwnProperty(parts[0])){
      receivers[parts[0]].disconnect()
    }
    io.to(parts[0]).emit("gdata", gdata)
    grec = redis.createClient()
    for(var i = 0;i<gdata.length;i++){
      var gnum = i
      var graph = gdata[i]
      for(var j = 0;j<graph.length;j++){
        var gseries = graph[j]
        grec.psubscribe(gseries))
        grec.on("pmessage", function(pattern, channel, message){
          if(pattern == gseries){
            io.to(parts[0]).emit("graph", {graph:gnum, series:channel})
          }
        })
      }
    }
  }
})

io.on('connection', function(socket){
  var page = ""
  socket.on('page', function(message){
    page = message.name
    socket.join(page)
    master.sadd("sketches",page, function(){
      master.smembers("sketches", function(err, sketches){
        socket.emit("sketches", sketches)
      })
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
  })
  socket.on('save', function(message){
    console.log("save",page+".code")
    master.set(page+".code",message.code)
  })
  socket.on('save_run', function(message){
    master.set(socket.page+".code",message.code,function(){
      master.publish("control", JSON.stringify({cmd:"start",name:page}))
    })
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
