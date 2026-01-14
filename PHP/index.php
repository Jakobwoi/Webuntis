<doctype html>
    <html>

    <head>
        <meta charset="utf-8">
        <title>Timetable</title>
    </head>

    <body>
    <?php
    include "WebUntis.php";
    $otp_code = $totp->now();
    login($login_url, $school, $user, $otp_code);
    echo get_timetable(5, $user_id, $session_id, time()+172800/2, time()+172800);
    ?>
    </body>
</html>