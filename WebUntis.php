<?php
require 'vendor/autoload.php';
include 'config.php';
use OTPHP\TOTP;

$login_url = $base_url . "/WebUntis/jsonrpc_intern.do?";

$api_url = $base_url . "/WebUntis/jsonrpc.do";

$totp = TOTP::create($secret, 30);

$user_type = ""; // student or teacher
$numeric_user_type = ""; // 2 = teacher, 5 = student
$user_id = ""; // numeric id

$session_id = ""; // jsessionid

$subjects = array();
$rooms = array();
$classes = array();
$timegrid = array();
$holidays = array();

function login($api_url, $school, $user, $otp)
{
    global $user_type, $user_id, $session_id, $subjects, $rooms, $classes, $timegrid, $holidays;
    $time = time() * 1000;
    $login_session = curl_init();
    $headers = array('Content-Type: application/json');

    $data = array(
        'id' => 'Awesome',
        'method' => 'getUserData2017',
        'params' => array(
            array(
                'auth' => array(
                    'clientTime' => $time, // Assuming $time is defined
                    'user' => $user,   // Assuming $username is defined
                    'otp' => $otp        // Assuming $token is defined
                )
            )
        ),
        'jsonrpc' => '2.0'
    );
    $params = array(
        'm' => 'getUserData2017',
        'school' => $school,
        'v' => 'i2.2',
    );
    curl_setopt($login_session, CURLOPT_URL, $api_url . '?' . http_build_query($params));
    curl_setopt($login_session, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($login_session, CURLOPT_HEADER, 1);
    curl_setopt($login_session, CURLOPT_POST, 1);
    curl_setopt($login_session, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($login_session, CURLOPT_HTTPHEADER, $headers);
    $response = curl_exec($login_session);
    $header_size = curl_getinfo($login_session, CURLINFO_HEADER_SIZE);
    $header = substr($response, 0, $header_size);
    $body = substr($response, $header_size);
    $body_json = json_decode($body, true);
    // Get user type and id, needed for timetable request
    $user_type = $body_json['result']['userData']['elemType'];
    $user_id = $body_json['result']['userData']['elemId'];
    // Get session cookie required for further requests
    preg_match_all('/Set-Cookie:\s*JSESSIONID\s*=\s*([^;]*)/mi', $header, $session_cookie);
    $session_id = $session_cookie[1][0];
    // Get all holidays, classes, rooms, subjects and the timegrid
    foreach ($body_json['result']['masterData']['holidays'] as $holiday) { // holidays
        $holidays[$holiday["id"]] = [
            'name' => $holiday['name'],
            'longName' => $holiday['longName'],
            'startDate' => $holiday['startDate'],
            'endDate' => $holiday['endDate']
        ];
    }
    ksort($holidays);
    foreach ($body_json['result']['masterData']['klassen'] as $class) { // classes
        $classes[$class["id"]] = [$class['name'], $class['longName']];
    }
    ksort($classes);
    foreach ($body_json['result']['masterData']['rooms'] as $room) { // rooms
        $rooms[$room["id"]] = $room['name'];
    }
    ksort($rooms);
    foreach ($body_json['result']['masterData']['subjects'] as $subject) { // subjects
        $subjects[$subject["id"]] = [$subject['name'], $subject['longName']];
    }
    ksort($subjects);
    foreach ($body_json['result']['masterData']['timeGrid']['days'][0]['units'] as $time) { // timegrid
        $timegrid[$time["label"]] = [
            'startTime' => ltrim($time['startTime'], 'T'),
            'endTime' => ltrim($time['endTime'], 'T')
        ];
    }
    ksort($timegrid);

    curl_close($login_session);
}
?>