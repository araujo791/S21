<?php
if( ! defined( 'ABSPATH' ) ){
	exit; // Exit if accessed directly
}
?>

<div id="mfn-custom" class="wrap about-wrap">

	<?php include_once( plugin_dir_path( __DIR__ ) . '/templates/parts/header.php' ); ?>

	<div class="dashboard-tab register">

		<div class="col mfn-ui">
			<form method="post" class="mfn-form">
				<?php
					$this->form_handler();
					$meta = false;
				?>

				<h3 class="primary"><?php __('Built-in features', 'becustom'); ?></h3>
				

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'disable_theme_version',
						'type' => 'switch',
						'title' => $this->get_attributes['disable_theme_version']['title'],
						'options' => array(
							0 => 'Visible',
							1 => 'Hidden'
						),
						'std' => '0',
						'desc' => $this->popup('disable_theme_version')
					), $this->options['disable_theme_version']['value'] ? 1 : 0, $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'disable_support_link',
						'type' => 'switch',
						'title' => $this->get_attributes['disable_support_link']['title'],
						'options' => array(
							0 => 'Visible',
							1 => 'Hidden'
						),
						'std' => '0',
						'desc' => $this->popup('disable_support_link')
					), $this->options['disable_support_link']['value'] ? 1 : 0, $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'disable_changelog_link',
						'type' => 'switch',
						'title' => $this->get_attributes['disable_changelog_link']['title'],
						'options' => array(
							0 => 'Visible',
							1 => 'Hidden'
						),
						'std' => '0',
						'desc' => $this->popup('disable_changelog_link')
					), $this->options['disable_changelog_link']['value'] ? 1 : 0, $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'disable_theme_update',
						'type' => 'switch',
						'title' => $this->get_attributes['disable_theme_update']['title'],
						'options' => array(
							0 => 'Visible',
							1 => 'Hidden'
						),
						'std' => '0',
						'desc' => $this->popup('disable_theme_update')
					), $this->options['disable_theme_update']['value'] ? 1 : 0, $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'disable_advanced_tab',
						'type' => 'switch',
						'title' => $this->get_attributes['disable_advanced_tab']['title'],
						'options' => array(
							0 => 'Visible',
							1 => 'Hidden'
						),
						'std' => '0',
						'desc' => $this->popup('disable_advanced_tab')
					), $this->options['disable_advanced_tab']['value'] ? 1 : 0, $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'disable_hooks_tab',
						'type' => 'switch',
						'title' => $this->get_attributes['disable_hooks_tab']['title'],
						'options' => array(
							0 => 'Visible',
							1 => 'Hidden'
						),
						'std' => '0',
						'desc' => $this->popup('disable_hooks_tab')
					), $this->options['disable_hooks_tab']['value'] ? 1 : 0, $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'disable_footer_copy',
						'type' => 'switch',
						'title' => $this->get_attributes['disable_footer_copy']['title'],
						'options' => array(
							0 => 'Visible',
							1 => 'Hidden'
						),
						'std' => '0',
						'desc' => $this->popup('disable_footer_copy')
					), $this->options['disable_footer_copy']['value'] ? 1 : 0 , $meta)
				?>

				<?php wp_nonce_field('becustom_nonce') ?>
				<?php submit_button( __('Save changes', 'becustom') );  ?>
			</form>
		</div>
	</div>

</div>
