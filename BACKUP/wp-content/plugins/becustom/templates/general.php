<?php
if( ! defined( 'ABSPATH' ) ){
	exit; // Exit if accessed directly
}
?>

<div id="mfn-custom" class="wrap about-wrap">

	<?php include_once( plugin_dir_path( __DIR__ ) . '/templates/parts/header.php' ); ?>

	<div class="dashboard-tab">

		<div class="col">

		<?php
			if( WHITE_LABEL ){
				echo __('<h3>White label activated, all of the settings are disabled</h3>', 'becustom');
			}
		?>

		<p> <?php echo __('BeCustom is provided exclusively for Betheme customers only.', 'becustom'); ?></p>

		<p> <?php echo __('This tool allows to re-brand Be into a totally custom product that you may be proud of while providing it for your customers.', 'becustom'); ?></p>

		<p> <?php echo __('Replace any Betheme and Muffin Group logos to own, change any occurrence of "Be" or even customise the WP login page in a very simple way.', 'becustom'); ?></p>

		<p> <?php echo __('It is so simple that you will be surprised.', 'becustom'); ?></p>

		</div>

	</div>

</div>
