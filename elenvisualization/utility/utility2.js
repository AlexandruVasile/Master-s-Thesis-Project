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
            y: parseFloat(data[i][no_dataset_columns - 2]),
            lineDashType: "dot"
        });
        dataPoints3.push({
            x: new Date(data[i][date_index]),
            y: parseFloat(data[i][no_dataset_columns - 1]),
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

    // create the chart
    var chart = new CanvasJS.Chart(divId, {
        animationEnabled: true,
        theme: "light2",
        zoomEnabled: true,
        title: {
            text: y_label + " over time"
        },

        axisY:
            [{
                title: y_label,
                titleFontSize: 24,

            },

            ],
        axisY2: [{
            title: "Bitcoin's value",
            titleFontSize: 24

        },
        {
            title: "Bitcoin's TV",
            titleFontSize: 24
        },
        {
            title: "Bitcoin's fee",
            titleFontSize: 24
        }
        ],
        legend: {
            verticalAlign: "top",
            fontSize: 16,
            dockInsidePlotArea: false,
            cursor: "pointer",
            itemclick: toggleDataSeries
        },
        data:
            [
                {
                    type: "spline", //Change it to "spline", "area", "column"
                    lineThickness: 3,
                    showInLegend: true,
                    name: y_label,
                    dataPoints: dataPoints,

                },
                {
                    type: "spline", //Change it to "spline", "area", "column"
                    axisYType: "secondary",
                    showInLegend: true,
                    name: "Bitcoin's value",
                    dataPoints: dataPoints2,
                    color: "orange",
                    markerSize: 0

                },
                {
                    type: "spline", //Change it to "spline", "area", "column"
                    axisYType: "secondary",
                    axisYIndex: 1, //Defaults to Zero
                    showInLegend: true,
                    name: "Bitcoin's TV",
                    dataPoints: dataPoints3,
                    color: "grey",
                    markerSize: 0
                },
                {
                    type: "spline", //Change it to "spline", "area", "column"
                    axisYType: "secondary",
                    axisYIndex: 2, //Defaults to Zero
                    showInLegend: true,
                    name: "Bitcoin's fee",
                    dataPoints: dataPoints4,
                    color: "blue",
                    markerSize: 0
                }
            ]
    });

    // render the chart
    chart.render();
    function toggleDataSeries(e) {
        if (typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible)
            e.dataSeries.visible = false;
        else
            e.dataSeries.visible = true;
        chart.render();
    }
}