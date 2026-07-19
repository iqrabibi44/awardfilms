<?php
/**
 * Shared PDO MySQL connection — AwardFilms API
 * XAMPP: 127.0.0.1:3306, root, no password
 */
class DB
{
    private static ?PDO $instance = null;

    public static function connection(): PDO
    {
        if (self::$instance === null) {
            $dsn  = 'mysql:host=127.0.0.1;port=3306;dbname=awardfilms_db;charset=utf8mb4';
            $user = 'root';
            $pass = '';

            self::$instance = new PDO($dsn, $user, $pass, [
                PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES   => false,
            ]);
            self::$instance->exec("SET NAMES utf8mb4");
        }
        return self::$instance;
    }
}
