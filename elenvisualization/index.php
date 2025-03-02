<?php 
include 'common/top_page.php';
include 'utility/utility.php';

# create a white list to avoid path traversal 
$data_directory = 'website_data';
$whitelist = createWhiteList($data_directory);

# load the json file about the navigational bar structure
$nav_bar_structure_json = file_get_contents($data_directory.'/aux_data/nav_bar_structure.json');
$nav_bar_structure = json_decode($nav_bar_structure_json, true);
?>

<!-- create dynamically the navigation bar -->
<nav>
	<ul class="noBulletsOnList nav noPaddingMargin">
		<?php foreach ($nav_bar_structure as $item): ?>
			<li id="<?= $item['id'] ?>" onclick="toggleSubOptions('<?= $item['id'] ?>')">
				<?php if (count($item['sub-options']) === 1): ?>
					<a href='index.php?option=<?= $item['id'] . "_" . $item['sub-options'][0] ?>'><?= $item['label'] ?></a>
				<?php else: ?>
					<a><?= $item['label'] ?></a>
				<?php endif; ?>
			</li>
		<?php endforeach; ?>
    </ul>
	<div class="chartContainerList"></div>
</nav><br><br><br>

<script>
    const chartContainerList = document.querySelector(".chartContainerList");
    var options = <?= $nav_bar_structure_json; ?>;

    function getOptionIndex(optionId){
        for (let i = 0; i < options.length; i++){
            if(options[i].id == optionId)
                return i;
            console.log(optionId);
        }
        return -1;
    }

    // create the value that needs to be give to the query string parameter option
    function createOptionParameterValue(id, sub_option) {
        res = id + "_" + sub_option.replace(/\s+/g, '_');
        return res;
    }
    
    // toggle the sub-section area of a certain option of the navigation bar
    function toggleSubOptions(optionId) {
        var optionIndex = getOptionIndex(optionId); 
        var resHTML = '';
        
        // if the button was already clicked then remove the suboptions
        if(options[optionIndex]['already-clicked']){
            chartContainerList.innerHTML = resHTML; 
            for (let i = 0; i < options.length; i++)
                options[i]['already-clicked'] = false;
            return;
        }
        
        // create the sub-options section
        var subOptions = options[optionIndex]['sub-options'];
        
        resHTML += '<ul class="noBulletsOnList nav2 noPaddingMargin">';
        if(subOptions.length > 1)
            for (let i = 0; i < subOptions.length; i++){
                option = createOptionParameterValue(optionId, subOptions[i])
                console.log(option);
                resHTML += '<li><a href="index.php?option='+ option +'" >'+subOptions[i]+'</a></li>'; 
                
            }
            resHTML += '</ul';
            chartContainerList.innerHTML += resHTML;

        options[optionIndex]['already-clicked'] = true;
    }
</script>

<?php
// if an option from the navigational bar was selected then ..
if (isset($_GET['option'])){
    // build the dataset and correlation matrix paths from the GET parameter option
    
    $dataset_path = $_GET['option']."_dataset.csv";
    $correlation_matrix_path = $_GET['option']."_correlation_matrix.csv";

    // validate paths against the whitelist to avoid path traversal
    if (in_array($dataset_path, $whitelist) AND in_array($correlation_matrix_path, $whitelist)) {
        // build the full paths
        $dataset_path = $data_directory . '/' . $dataset_path;
        $correlation_matrix_path = $data_directory . '/' . $correlation_matrix_path;
    } else{
        echo "<h3>The inserted option is not available</h3>";
        include 'common/bottom_page.php';
        exit;
    }
} 
else{
    // if none option was selected then show longitudinal ln statistics
    $dataset_path = $data_directory . '/ln_graph_stats_dataset.csv';
    $correlation_matrix_path = $data_directory . '/ln_graph_stats_correlation_matrix.csv';
}
?>

<?php

// import the csv dataset as an array of arrays of strings, each string is a an element of the csv file
$dataset = array_map('str_getcsv', file($dataset_path));

// turn the dataset into json to use it in JavaScript
$dataset_json = json_encode($dataset);

// import the correlation matrix
$correlation_matrix = array_map('str_getcsv', file($correlation_matrix_path));


// create a chart for each column of the dataset
$no_dataset_columns = count($dataset[0]);
$date_column_index = findStringIndex($dataset[0], "date");
$transaction_volume_column_index = findStringIndex($dataset[0], "transaction volume");
$market_price_column_index = findStringIndex($dataset[0], "market price");
$average_fee_column_index = findStringIndex($dataset[0], "average fee");

$is_date_skipped = 0;





for ($i = 0; $i < $no_dataset_columns; $i++) {
    // skip charting for date, transaction volume, market price and average fee
    if (in_array($i, [$date_column_index, $transaction_volume_column_index, $market_price_column_index, $average_fee_column_index])) {
        $is_date_skipped = 1;
        continue;
    }

    // get the correlation value of the current column with the market price and the transaction volume
    $market_price_correlation = $correlation_matrix[$i+1-$is_date_skipped][$market_price_column_index];
    $transaction_volume_correlation = $correlation_matrix[$i+1-$is_date_skipped][$transaction_volume_column_index];
    $average_fee_correlation = $correlation_matrix[$i+1-$is_date_skipped][$average_fee_column_index];

    // associate a color to the correlation values
    $market_price_color = getColorForCorrelation($market_price_correlation);
    $transaction_volume_color = getColorForCorrelation($transaction_volume_correlation);
    $average_fee_color = getColorForCorrelation($average_fee_correlation);

    // generate a chart container and a script that creates a chart
    echo '<div id="chartContainer' . $i . '" class="chart flex-item""></div>';


    echo '<script> createChart(' . $dataset_json .', "chartContainer'.$i.'",'.$i.','. $date_column_index . ','. $no_dataset_columns .') </script>';

    // display correlation values with colored numbers
    echo '<div class="chartBottomSide flex-item">
            <h3>Correlation with Bitcoin\'s value: <span style="color: ' . $market_price_color. ';">' . $market_price_correlation . '</span></h3>
            <h3>Correlation with Bitcoin\'s TV: <span style="color: ' . $transaction_volume_color . ';">' . $transaction_volume_correlation . '</span></h3>
            <h3>Correlation with Bitcoin\'s average fee: <span style="color: ' . $average_fee_color . ';">' . $average_fee_correlation . '</span></h3>
        </div><br><br><br><br>';
}


// plot attacks



$elements = explode("_", $_GET['option']);

// Check if the first element is "attacks"
if ($elements[0] === "attacks") {
    // generate a chart container and a script that creates a chart

    // generate fraction values
    // Extract first row (headers)
    $headers = $dataset[0];

    // Array to store fractions
    $fractionLabels = [];

    // Loop through headers and extract fractions
    foreach ($headers as $header) {
        if (strpos($header, 'diameter_with_fraction_') !== false) {
            // Extract the number part
            $parts = explode('_', $header);
            $fractionLabels[] = end($parts);
        }
    }

    // turn the dataset into json to use it in JavaScript
    $fractionLabelsJson = json_encode($fractionLabels);
    $starting_row = 1;   
    $is_gc = 1;
    $step =  9; # how many curves per graph
    $no_rows = count($dataset);

    for ($i = 0; $i < 2; $i++) {
        for ($j = 1; $j < $no_rows; $j+=$step) {
            echo '<div id="chartContainerB' . $i . "_" . $j . '" class="chart flex-item""></div>';
            echo '<script> createChartB(' . $i . ',' . $fractionLabelsJson . ',' . $dataset_json .', "chartContainerB' . $i . "_" . $j . '",' . $date_column_index . ',' . $j . ',' . ($j+$step) . ') </script>';
        }
    }
} 
?>
<?php include 'common/bottom_page.php'; ?>
