<?php
if( ! defined( 'ABSPATH' ) ){
	exit; // Exit if accessed directly
}
?>

<div id="mfn-custom" class="wrap about-wrap">

	<?php include_once( plugin_dir_path( __DIR__ ) . '/templates/parts/header.php' ); ?>

	<div class="dashboard-tab">

		<div class="col">
			<?php if( mfn_is_registered() ): ?>

				<h3 class="primary"><?php __( 'Theme is registered', 'becustom' ); ?></h3>

				<form class="form-register form-deregister" method="post">

					<?php settings_fields( 'betheme_registration' ); ?>

					<p>
						<code><?php echo mfn_get_purchase_code_hidden(); ?></code>
					</p>

					<?php if( mfn_is_hosted() ): ?>

						<p class="confirm deregister" style="margin-bottom:40px">
							<?php echo __('You are using Envato Hosted, this subscription code can not be deregistered.', 'becustom'); ?>
						</p>

					<?php else: ?>

						<p class="confirm deregister">
							<a class="mfn-button mfn-button-primary mfn-button-fw"><?php echo __( 'Deregister Theme', 'becustom' ); ?></a>
						</p>

					<?php endif; ?>

					<?php if( WHITE_LABEL ): ?>

						<p class="question"><?php echo __( 'This feature is disabled in White Label mode.', 'mfn-opts' );?></p>

					<?php else: ?>

						<p class="question">
							<?php $this->deregister(); ?>
							<input type="input" hidden name="action_name" value="deregister" />
							<span><?php echo __( 'Are you sure you want to deregister the theme?', 'becustom' ); ?></span>
							<a class="mfn-button cancel" target="_blank" href="#"><?php echo __( 'Cancel', 'becustom' ); ?></a>
							<input type="submit" class="mfn-button mfn-button-primary" name="deregister" value="<?php echo __( 'Deregister', 'becustom' ); ?>" />
						</p>

					<?php endif; ?>

				</form>

				<p class="check-licenses"><a target="_blank" href="http://api.muffingroup.com/licenses/"> <?php echo __('Check your licenses', 'becustom'); ?> </a></p>

			<?php endif; ?>			

			<h3 class="primary"> <?php __('Import/Export settings', 'becustom'); ?> </h3>
			<form class="form-import form-export" method="post">
				<textarea class="becustom-import-export" name="importexport"></textarea>
				
				<input type="input" hidden name="action_name" value="import" />
				<input type="input" hidden id="export-content" name="export-content" value="<?php echo $this->export_options() ?>" />
				<input type="input" hidden id="import-content" name="import-content" value="" />
				<?php $this->import_options(); ?>

				<br />
				<input type="submit" class="mfn-button mfn-button-primary" name="import" disabled value="<?php echo __( 'Import', 'becustom' ); ?>" />
				<input type="submit" class="mfn-button mfn-button-primary" name="export" disabled value="<?php echo __( 'Export', 'becustom' ); ?>" />
			</form>

		</div>
	</div>

</div>
