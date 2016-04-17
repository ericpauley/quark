var socket = io();

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

window.onload = function () {
	var chart = new CanvasJS.Chart("chartContainer",
	{
		animationEnabled: true,
		title:{
			text: "Example Graph"
		},
		data: [
		{
			type: "spline", //change type to bar, line, area, pie, etc
			showInLegend: true,        
			dataPoints: [
				{ x: 10, y: 51 },
				{ x: 20, y: 45},
				{ x: 30, y: 50 },
				{ x: 40, y: 62 },
				{ x: 50, y: 95 },
				{ x: 60, y: 66 },
				{ x: 70, y: 24 },
				{ x: 80, y: 32 },
				{ x: 90, y: 16}
			]
			},
			{
			type: "spline",
			showInLegend: true,        
			dataPoints: [
				{ x: 10, y: 21 },
				{ x: 20, y: 44},
				{ x: 30, y: 35 },
				{ x: 40, y: 45 },
				{ x: 50, y: 75 },
				{ x: 60, y: 58 },
				{ x: 70, y: 18 },
				{ x: 80, y: 30 },
				{ x: 90, y: 11}
			]
			}
		],
		legend: {
			cursor: "pointer",
			itemclick: function (e) {
				if (typeof(e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
					e.dataSeries.visible = false;
				} else {
					e.dataSeries.visible = true;
			}
			chart.render();
			}
		}
	});

	chart.render();
}