var myCode = editor.getValue();
var socket = io();
var list = document.getElementById("sketchList");


loaded = false

editor.setReadOnly(true);

socket.on("connect",function(){
  page = window.location.pathname
  page = /\/(\w+)/.exec(page)[1]
  $("#loglink").attr("href",page+"/logs")
  console.log(page)
  socket.emit("page", {name:page})
  document.getElementById("sketchDropDown").innerHTML = page;
})

socket.on("page", function(message){
  loaded = true
  editor.setReadOnly(false)
  autoupdate = true
  editor.setValue(message.code);
  autoupdate = false
})

socket.on("sketches", function(sketches){
  $("#sketchList").empty()
  for (i = 0; i < sketches.length; i++) {
    $("#sketchList").append('<li><a href="/'+sketches[i]+'">'+sketches[i]+'</a></li>')
  }
})

gdata = []
graphs = []
charts = []

autoupdate = false

socket.on("logs", function(message){
  $("#log-messages").prepend('<p><pre class="bg-'+message.type+'">'+message.text+'</pre></p>')
})

$("#log-messages").prepend('<p class="bg-info">Log messages from your program will appear here.</p>')

socket.on("gdata", function(gd){
  console.log("Ayoo", gd)
  gdata = gd
  graphs = []
  charts = []
  $("#view-body").empty()
  for(var i = 0;i<gdata.length;i++){
    console.log(i)
    graphs.push({})
    $("#view-body").append('<div id="chart-'+i+'" style="height: 300px; width: 100%;"></div>')
    var chart = new CanvasJS.Chart("chart-"+i,
  	{
  		animationEnabled: true,
  		title:{
  			text: gdata[i].title
  		},
  		data: [],
  		legend: {}
  	});
    charts.push(chart);
    chart.render()
  }
})

socket.on("devices", function(data){
  $("#device-list").empty()
  for(var key in data){
    $("#device-list").append("<p>Device "+key+" mapped to device id "+data[key])
  }
  console.log("devices", data || {})
})

socket.on("graph", function(graph){
  graph.t *= 1000
  g=graphs[graph.graph]
  if(!g[graph.series]){
    d = {
			type: "line",
      xValueType: "dateTime",
      markerType: "none",
      legendText: graph.series,
			showInLegend: true,
			dataPoints: []
    }
    g[graph.series] = d.dataPoints
    charts[graph.graph].options.data.push(d)
  }
  var index = g[graph.series].length
  console.log(g[graph.series][index-1],graph)
  while(index > 0 && g[graph.series][index-1].t > graph.t){
    console.log("backtrack")
    index--
  }
  g[graph.series].splice(index,0,{x:graph.t,y:graph.val})
  while(g[graph.series].length > 100){
    g[graph.series].shift()
  }
})

setInterval(function(){
  for(var i = 0;i<charts.length;i++){
    charts[i].render()
  }
},1000/60)

socket.on("running", function(running){
  console.log("running", running)
  if(running != "0"){
    $("#stop").text("Stop").prop("disabled", false)
  }else{
    $("#stop").text("Stopped").prop("disabled", true)
  }
})

editor.on("change", function(){
  if(!autoupdate)
    socket.emit("save", {code:editor.getValue()})
})

window.onload = function() {
}


function runCode(){
  socket.emit("save_run",{code:editor.getValue()})
}

function stopCode(){
  socket.emit("stop")
}

function newSketch(){
  newSketch = document.getElementById("newSketchName").value
  console.log(newSketch);
  var baseURL = "/";
  newURL = baseURL.concat(newSketch);
  console.log(newURL);
  document.getElementById("newSketchName").placeholder = newSketch;
  window.location.href = newURL;
}

function associate(){
  console.log($("#id_field").val())
  console.log($("#name_field").val())
  socket.emit("associate", {id:$("#id_field").val(),name:$("#name_field").val()})
}
