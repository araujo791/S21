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

				<h3 class="primary"><?php echo __('Branding', 'becustom'); ?></h3>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'betheme_label',
						'type' => 'text',
						'title' => $this->get_attributes['betheme_label']['title'],
						'std' => 'betheme',
						'desc' => $this->popup('betheme_label')
					), $this->options['betheme_label']['value'] , $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'betheme_url_slug',
						'type' => 'text',
						'title' => $this->get_attributes['betheme_url_slug']['title'],
						'std' => 'be',
						'desc' => $this->popup('betheme_url_slug')
					), $this->options['betheme_url_slug']['value'] , $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'replaced_logo_url',
						'type' => 'upload',
						'title' => $this->get_attributes['replaced_logo_url']['title'],
						'std' => '',
						'preview' => 'image',
						'desc' => $this->popup('replaced_logo_url')
					), $this->options['replaced_logo_url']['value'] , $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'replaced_theme_image',
						'type' => 'upload',
						'title' => $this->get_attributes['replaced_theme_image']['title'],
						'std' => '',
						'preview' => 'image',
						'desc' =>  $this->popup('replaced_theme_image')
					), $this->options['replaced_theme_image']['value'] , $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'replaced_theme_desc',
						'type' => 'text',
						'title' => $this->get_attributes['replaced_theme_desc']['title'],
						'std' => '',
						'desc' => $this->popup('replaced_theme_desc')
					), $this->options['replaced_theme_desc']['value'] , $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'replaced_theme_author',
						'type' => 'text',
						'title' => $this->get_attributes['replaced_theme_author']['title'],
						'std' => '',
						'desc' => $this->popup('replaced_theme_author')
					), $this->options['replaced_theme_author']['value'] , $meta)
				?>

				<?php wp_nonce_field('becustom_nonce') ?>
				<?php submit_button( __('Save changes', 'becustom') );  ?>
			</form>
		</div>
	</div>

</div>
