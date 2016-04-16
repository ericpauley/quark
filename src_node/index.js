express = require('express')

var app = express()
var http = require('http').Server(app)
app.use(express.static('html'))

app.get('/', function(req, res){
  res.send('<h1>Hello world</h1>')
});

http.listen(3000, function(){
  console.log('listening on *:3000')
});
