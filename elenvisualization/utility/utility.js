function createChart(data, divId, index, date_index, no_dataset_columns) {

    // create the data points
    var dataPoints = [];
    var dataPoints2 = [];
    var dataPoints3 = [];
    var dataPoints4 = [];
    var x_axis = [];
    for (var i = 1; i < data.length; i++) {    // i=1 since we need to skip the columns when iterating through the rows
        x_axis.push(new Date(data[i][date_index]));
        dataPoints.push({
            x: new Date(data[i][date_index]),
            y: parseFloat(data[i][index])
        });
        dataPoints2.push({
            x: new Date(data[i][date_index]),
            y: parseFloat(data[i][no_dataset_columns - 3]),
            lineDashType: "dot"
        });
        dataPoints3.push({
            x: new Date(data[i][date_index]),
            y: parseFloat(data[i][no_dataset_columns - 2]),
            lineDashType: "dot"
        });
        dataPoints4.push({
            x: new Date(data[i][date_index]),
            y: parseFloat(data[i][no_dataset_columns - 1]),
            lineDashType: "dot"
        });
    }

    // create the y label
    var y_label = data[0][index].replace(/_/g, ' ');

    var stockChart = new CanvasJS.StockChart(divId, {
        zoomEnabled: true,
        exportEnabled: true,
        animationEnabled: true,
        theme: "light2",
        title: {
            text: y_label + " over time"
        },


        charts: [
            {
                axisX: {
                    labelAngle: -30
                },
                axisY: [{
                    title: y_label,
                    gridThickness: 1,  // Enable gridlines for the primary Y axis
                    titleFontSize: 24,
                }],
                axisY2: [
                    {
                        title: "Bitcoin's value",
                        gridThickness: 1,
                        titleFontSize: 24,
                        labelFormatter: function (e) {
                            return "$" + CanvasJS.formatNumber(e.value, "#,##0");  // Remove decimal places
                        }
                    },
                    {
                        title: "Bitcoin's TV",
                        gridThickness: 1,
                        titleFontSize: 24,
                    },
                    {
                        title: "Bitcoin's fee",
                        gridThickness: 1,
                        titleFontSize: 24,
                        labelFormatter: function (e) {
                            return "$" + CanvasJS.formatNumber(e.value, "#,##0");  // Remove decimal places
                        }
                    }
                ],
                legend: {
                    verticalAlign: "top",
                    fontSize: 16,
                    dockInsidePlotArea: false,
                    cursor: "pointer",
                    itemclick: toggleDataSeries
                },
                data: [
                    {
                        type: "line",
                        lineThickness: 3,
                        showInLegend: true,
                        name: y_label,
                        dataPoints: dataPoints,
                        // markerType: "circle",
                        // markerSize: 8
                    },
                    {
                        type: "line",
                        axisYType: "secondary",
                        showInLegend: true,
                        name: "Bitcoin's value",
                        dataPoints: dataPoints2,
                        color: "black",
                        markerSize: 0
                    },
                    {
                        type: "line",
                        axisYType: "secondary",
                        axisYIndex: 1,
                        showInLegend: true,
                        name: "Bitcoin's TV",
                        dataPoints: dataPoints3,
                        color: "grey",
                        markerSize: 0
                    },
                    {
                        type: "line",
                        axisYType: "secondary",
                        axisYIndex: 2,
                        showInLegend: true,
                        name: "Bitcoin's fee",
                        dataPoints: dataPoints4,
                        color: "blue",
                        markerSize: 0
                    }
                ]
            }
        ],
        toolTip: {
            shared: true,
            content: function (e) {
                var content = "<strong>" + CanvasJS.formatDate(e.entries[0].dataPoint.x, "MMM DD YYYY") + "</strong>";
                for (var i = 0; i < e.entries.length; i++) {
                    content += "<br/><span style='color:" + e.entries[i].dataSeries.color + "'>" + e.entries[i].dataSeries.name + "</span>: " +
                        ((e.entries[i].dataSeries.name === "Bitcoin's value" || e.entries[i].dataSeries.name === "Bitcoin's fee") ? "$" : "") +
                        CanvasJS.formatNumber(e.entries[i].dataPoint.y, "#,##0");  // Remove decimal places
                }
                return content;
            }
        },
        navigator: {
            enabled: true,
            slider: {
                minimum: dataPoints[0].x,
                maximum: dataPoints[dataPoints.length - 1].x
            }
        }
    });
    stockChart.render();

    function toggleDataSeries(e) {
        if (typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible)
            e.dataSeries.visible = false;
        else
            e.dataSeries.visible = true;
        stockChart.render();
    }
}



function generateBlueShades(numCurves) {
    var colors = [];
    var hue = 210; // This represents the blue hue
    var saturation = 100; // 100% saturation for vibrant colors

    // Start from a low lightness (darker blue) and increase it for each curve
    var minLightness = 20;  // Dark blue
    var maxLightness = 80;  // Light blue

    // Calculate the step increment for lightness based on the number of curves
    var lightnessStep = (maxLightness - minLightness) / (numCurves - 1);

    for (var i = 0; i < numCurves; i++) {
        // Calculate the lightness for the current curve
        var lightness = minLightness + (lightnessStep * i);

        // Generate the HSL color string and push it to the array
        var color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
        colors.push(color);
    }

    return colors;
}


function createChartB(is_gc, fractionLabels, dataset, divId, date_index, starting_row, ending_row) {
    console.log("----ciaociaociao----")
    console.log(dataset)
    console.log("----ciaociaociao----")

    console.log("Ending row:");
    console.log(ending_row);
    console.log("Ending row:");
    if (ending_row > dataset.length)
        ending_row = dataset.length;
    var blueShades = generateBlueShades(ending_row - starting_row);
    var data = [];
    var plot =
    {
        type: "spline",
        name: "",
        markerSize: 10,
        axisYType: "secondary",
        //xValueFormatString: "YYYY",

        showInLegend: true,
        dataPoints: []
    }


    var no_columns = fractionLabels.length;
    console.log(ending_row);
    for (var row = starting_row; row < ending_row; row++) {
        var curve = [];
        for (var column = 0; column < no_columns; column++) {
            curve.push({
                x: parseFloat(fractionLabels[column]),
                y: parseFloat(dataset[row][column + (no_columns * is_gc)]),
                //lineDashType: "dot"
            });
        }
        // Create a new plot object for each row
        console.log("==[[==");
        console.log(row);
        console.log("==[[==");
        var plot = {
            type: "spline",
            name: dataset[row][date_index],
            markerSize: 0.1,
            axisYType: "secondary",
            //xValueFormatString: "YYYY",
            showInLegend: true,
            dataPoints: curve,
            color: blueShades[row - starting_row]
        };
        data.push(plot);
    }
    console.log("--__--");
    console.log(data);
    console.log("---");

    var chart = new CanvasJS.Chart(divId, {
        theme: "light2", // "light1", "light2", "dark1", "dark2"
        animationEnabled: true,
        title: {
            text: is_gc === 1 ? "giant component over fraction removed nodes" : "diameter over fraction removed nodes"
        },

        axisX: {
            lineColor: "black",
            labelFontColor: "black"
        },
        axisY2: {
            gridThickness: 2,
            title: is_gc === 1 ? "giant component size" : "diameter",
            titleFontColor: "black",
            labelFontColor: "black"
        },
        legend: {
            cursor: "pointer",
            itemmouseover: function (e) {
                e.dataSeries.lineThickness = e.chart.data[e.dataSeriesIndex].lineThickness * 2;
                e.dataSeries.markerSize = e.chart.data[e.dataSeriesIndex].markerSize + 2;
                e.chart.render();
            },
            itemmouseout: function (e) {
                e.dataSeries.lineThickness = e.chart.data[e.dataSeriesIndex].lineThickness / 2;
                e.dataSeries.markerSize = e.chart.data[e.dataSeriesIndex].markerSize - 2;
                e.chart.render();
            },
            itemclick: function (e) {
                if (typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
                    e.dataSeries.visible = false;
                } else {
                    e.dataSeries.visible = true;
                }
                e.chart.render();
            }
        },
        toolTip: {
            shared: true
        },
        data: data
    });
    chart.render();
}