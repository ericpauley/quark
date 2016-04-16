express = require('express')

var app = express()
var http = require('http').Server(app)
app.use(express.static('html'))

var redis = require("redis"),
master = redis.createClient();
receiver = redis.createClient();

var io = require('socket.io')(http);

io.on('connection', function(socket){
  socket.on('page', function(message){
    socket.page = message.name
    console.log(socket.page)
    master.get(socket.page+".code", function(err,code){
      console.log(socket.page+".code",code)
      if(code != null){
        socket.emit('page', {code:code})
      }
    })
  })
  socket.on('save', function(message){
    master.set(socket.page+"code",message.code)
  })
  socket.on('save_run', function(message){
    master.set(socket.page+"code",message.code,function(){
      master.publish("control", JSON.stringify({cmd:"start",name:socket.page}))
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
