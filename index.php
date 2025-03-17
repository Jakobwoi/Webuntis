<doctype html>
    <html>

    <head>
        <meta charset="utf-8">
        <title>Timetable</title>
    </head>

    <body>
    <?php
    include 'WebUntis.php';
    login($login_url, $school, $user, $totp->now());
    ?>
    </body>
</html>