<?php

// function to find the index of a string in an array
function findStringIndex($array, $string) {
    return array_search($string, $array) ?? -1;
}

// function to determine the color based on the correlation value
function getColorForCorrelation($value) {
    if ($value >= -0.3 && $value <= 0.3)
        return 'green';
    elseif (($value > 0.3 && $value <= 0.7) || ($value >= -0.7 && $value < -0.3))
        return 'orange';
    else
        return 'red';
}
// function getColorForCorrelation($value) {
//     // Calculate grayscale intensity based on how close the value is to -1 or 1
//     $intensity = (int)(255 * (1 - abs($value)));
//     return 'rgb(' . $intensity . ',' . $intensity . ',' . $intensity . ')';
// }



function createWhiteList($data_directory){
    // scan the directory and get all files
    $files = scandir($data_directory);
    // filter out '.' and '..' and any unwanted files
    $whitelist = array_filter($files, function($file) use ($data_directory) {
        $full_path = $data_directory . '/' . $file;
        return is_file($full_path) && $file[0] !== '.';
    });
    return $whitelist;
}
?>
