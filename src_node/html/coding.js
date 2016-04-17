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
  // TODO: Stylize sketch list
  console.log(sketches)
  for (i = 0; i < sketches.length; i++) {
    var node = document.createElement("LI");
    var link = document.createElement("A");              // Create a <li> node
    var textnode = document.createTextNode(sketches[i]);         // Create a text node
    link.appendChild(textnode);                              // Append the text to <li>
    node.appendChild(link);
    document.getElementById("sketchList").appendChild(node);
    baseURL = "/";
    href = baseURL.concat(sketches[i]);
    link.href = href;
  }

})

gdata = []
graphs = []
charts = []

socket.on("gdata", function(gd){
  console.log("Ayoo", gd)
  gdata = gd
  graphs = []
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

socket.on("graph", function(graph){
  console.log(graph)
  g=graphs[graph.graph]
  if(!g[graph.series]){
    d = {
			type: "line",
			showInLegend: true,
			dataPoints: []
    }
    g[graph.series] = d.dataPoints
    charts[graph.graph].options.data.push(d)
  }
  g[graph.series].push({x:graph.t,y:graph.val})
  charts[graph.graph].render()
})

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
