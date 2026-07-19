<?php

class Translator {
    private static $translations = [];
    private static $currentLang = 'en';
    private static $loaded = false;

    public static function init() {
        if (self::$loaded) return;

        // Determine language from cookie or default to en
        self::$currentLang = $_COOKIE['lang'] ?? 'en';
        
        // Prevent path traversal
        $langFile = basename(self::$currentLang) . '.json';
        $path = __DIR__ . '/../locales/' . $langFile;

        if (file_exists($path)) {
            $json = file_get_contents($path);
            $parsed = json_decode($json, true);
            if (is_array($parsed)) {
                self::$translations = $parsed;
            }
        }
        self::$loaded = true;
    }

    public static function translate($text) {
        if (!self::$loaded) {
            self::init();
        }
        
        // Return exact translation if available
        if (isset(self::$translations[$text])) {
            return self::$translations[$text];
        }

        // Return original if no translation found
        return $text;
    }

    public static function getLang() {
        return self::$currentLang;
    }
}

// Global helper function for concise syntax in views
function __($text) {
    return Translator::translate($text);
}
