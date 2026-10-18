<?php header('Content-type: text/html; charset=ISO-8859-1');ini_set('display_errors', 0 );
error_reporting(0); include_once('mysql2i.class.php');
$host="localhost";
$dbname="sanesb04_site";
$usuario="sanesb04_banco";
$password='=J;FIPA=A3Du';

$con = mysql_connect($host,$usuario,$password);
$db=mysql_select_db($dbname,$con);
mysql_set_charset('Latin1');
?>
