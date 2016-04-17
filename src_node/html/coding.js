var myCode = editor.getValue();
var socket = io();
var list = document.getElementById("sketchList");


loaded = false

editor.setReadOnly(true);

socket.on("connect",function(){
  page = window.location.pathname
  page = /\/(\w+)/.exec(page)[1]
  console.log(page)
  socket.emit("page", {name:page})
  document.getElementById("sketchDropDown").innerHTML = page;
})

socket.on("page", function(message){
  loaded = true
  editor.setReadOnly(false)
  editor.setValue(message.code);
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

socket.on("gdata", function(gd){
  console.log("Ayoo", gd)
  gdata = gd
  graphs = []
  charts = []
  $("#view").empty()
  for(var i = 0;i<gdata.length;i++){
    console.log(i)
    graphs.push({})
    $("#view").append('<div id="chart-'+i+'" style="height: 300px; width: 100%;"></div>')
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
  console.log("devices", data || {})
})

socket.on("graph", function(graph){
  console.log(graph)
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
  g[graph.series].push({x:graph.t,y:graph.val})
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

setInterval(function(){
  if(loaded){
    socket.emit("save", {code:editor.getValue()})
  }
},1000)

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
