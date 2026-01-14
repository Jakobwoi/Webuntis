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
class subject
{
    public $id;
    public $name;
    public $longName;
    public $foreColor;
    public $backColor;
    public function __construct($id, $name = null, $longName = null, $foreColor = null, $backColor = null)
    {
        $this->id = $id;
        if ($name == null) {
            $name = 1;
        }
        $this->name = $name;
        $this->longName = $longName;
        $this->foreColor = $foreColor;
        $this->backColor = $backColor;
    }
}
class period
{
    public $startTime;
    public $endTime;
    public $subject;
    public $teacher;
    public $room;
}
/**
 * Login to the WebUntis API
 * @param string $api_url URL of the API
 * @param string $school School name
 * @param string $user Username
 * @param string $otp TOTP generated from the secret from the QR-Code for Untis-Mobile
 */
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

/** 
 * get the timetable of a room, class, teacher, subject or student
 * @param int $elemType 1 = class, 2 = teacher, 3 = subject, 4 = room or 5 = student, refers to 
 * @param int $elemId id of the selcted element
 * @param string $session_id login session id
 * @param int $startDateTime Timestamp of the start date
 * @param int $endDateTime Timestamp of the end date
 * @return bool|string
 */
function get_timetable($elemType, $elemId, $session_id, $startDateTime = null, $endDateTime = null): bool|string
{
    global $api_url;
    if ($startDateTime == null) {
        $startDateTime = time();
    }
    if ($endDateTime == null) {
        $endDateTime = time();
    }
    $timetable_session = curl_init();
    $headers = array(
        'Content-Type: application/json',
        'Cookie: JSESSIONID=' . $session_id
    );
    $data = array(
        'id' => 'get_timetable',
        'method' => 'getTimetable',
        'params' => [
            'options' => [
                'element' => [
                    'id' => $elemId,
                    'type' => $elemType,
                    'keyType' => 'id'
                ],
                'onlyBaseTimetable' => false,
                'showBooking' => true,
                'showInfo' => true,
                'showSubstText' => true,
                'showLsText' => true,
                'showStudentgroup' => true,
                'klasseFields' => ['id', 'name', 'longname'],
                'roomFields' => ['id', 'name', 'longname'],
                'subjectFields' => ['id', 'name', 'longname'],
                'startDate' => date('Ymd', $startDateTime),
                'endDate' => date('Ymd', $endDateTime)

            ]
        ],
        'jsonrpc' => '2.0'
    );

    curl_setopt($timetable_session, CURLOPT_URL, $api_url);
    curl_setopt($timetable_session, CURLOPT_POST, 1); // all api requests need to be POST
    curl_setopt($timetable_session, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($timetable_session, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($timetable_session, CURLOPT_HTTPHEADER, $headers);
    $response = curl_exec($timetable_session);
    curl_close(handle: $timetable_session);
    $json = json_decode($response, true);
    //echo json_encode($json["result"][1]);
    if (isset($json["result"])) {
        return json_encode($json["result"]);
    } else {
        return false;
    }
}
?>