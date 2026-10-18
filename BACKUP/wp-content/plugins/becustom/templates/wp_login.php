<?php
if( ! defined( 'ABSPATH' ) ){
	exit; // Exit if accessed directly
}
?>

<div id="mfn-custom" class="wrap about-wrap">

	<?php include_once( plugin_dir_path( __DIR__ ) . '/templates/parts/header.php' ); ?>

	<div class="dashboard-tab">
		<div class="col mfn-ui mfn-meta">

			<form method="post" class="mfn-form">
				<?php
					$this->form_handler(); //to enable form handler
					$meta = false;
				?>

				<h3 class="primary"> <?php __('WP Login', 'becustom'); ?></h3>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'enable_custom_login',
						'type' => 'switch',
						'title' => $this->get_attributes['enable_custom_login']['title'],
						'options' => array(
							1 => 'Yes',
							0 => 'No'
						),
						'std' => '1',
					), $this->options['enable_custom_login']['value'] ? 1 : 0, $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'custom_wplogin_logo',
						'type' => 'upload',
						'title' => $this->get_attributes['custom_wplogin_logo']['title'],
						'std' => 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/WordPress_blue_logo.svg/1024px-WordPress_blue_logo.svg.png',
						'preview' => 'image',
						'desc' => $this->popup('custom_wplogin_logo')
					), $this->options['custom_wplogin_logo']['value'] , $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
					'id' => 'custom_background_color',
					'type' => 'color',
					'title' => $this->get_attributes['custom_background_color']['title'],
					'desc' =>  $this->popup('custom_background_color'),
					'std' => '',
					), $this->options['custom_background_color']['value'], $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
					'id' => 'custom_font_color',
					'type' => 'color',
					'title' => $this->get_attributes['custom_font_color']['title'],
					'std' => '',
					'desc' => $this->popup('custom_font_color')
					), $this->options['custom_font_color']['value'], $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'custom_background_image',
						'type' => 'upload',
						'title' => $this->get_attributes['custom_background_image']['title'],
						'std' => '',
						'preview' => 'image',
						'desc' => $this->popup('custom_background_image')
					), $this->options['custom_background_image']['value'] , $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'custom_background_size',
						'type' => 'select',
						'title' => $this->get_attributes['custom_background_size']['title'],
						'options' => mfna_bg_size(),
						//'desc' =>  $this->popup('custom_background_size')
					), $this->options['custom_background_size']['value'] , $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'custom_background_position',
						'type' => 'select',
						'title' => $this->get_attributes['custom_background_position']['title'],
						'options' => mfna_bg_position(),
						//'desc' =>  $this->popup('custom_background_position')
					), $this->options['custom_background_position']['value'] , $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'custom_login_container_position',
						'type' => 'switch',
						'title' => $this->get_attributes['custom_login_container_position']['title'],
						'options' => array(
							'left' => "Left",
							'unset' => "Center",
							'right' => "Right"
						),
						//'desc' => "Where the content should appear on page",
						'std' => 'unset',
						//'desc' =>  $this->popup('custom_login_container_position')
					), $this->options['custom_login_container_position']['value'] , $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
					'id' => 'custom_login_container_background',
					'type' => 'color',
					'title' => $this->get_attributes['custom_login_container_background']['title'],
					'std' => '',
					'desc' => $this->popup('custom_login_container_background')
					), $this->options['custom_login_container_background']['value'], $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
					'id' => 'custom_login_container_font_color',
					'type' => 'color',
					'title' => $this->get_attributes['custom_login_container_font_color']['title'],
					'std' => '',
					'desc' =>  $this->popup('custom_login_container_font_color')
					), $this->options['custom_login_container_font_color']['value'], $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
					'id' => 'custom_login_container_input_background',
					'type' => 'color',
					'title' => $this->get_attributes['custom_login_container_input_background']['title'],
					'std' => '',
					'desc' =>  $this->popup('custom_login_container_input_background')
					), $this->options['custom_login_container_input_background']['value'], $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
					'id' => 'custom_login_container_input_font_color',
					'type' => 'color',
					'title' => $this->get_attributes['custom_login_container_input_font_color']['title'],
					'std' => '',
					'desc' => $this->popup('custom_login_container_input_font_color')
					), $this->options['custom_login_container_input_font_color']['value'], $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'enable_forgot_password',
						'type' => 'switch',
						'title' => $this->get_attributes['enable_forgot_password']['title'], 
						'options' => array(
							1 => 'Enable',
							0 => 'Disable'
						),
						'std' => '1',
						'desc' => $this->popup('enable_forgot_password')
					), $this->options['enable_forgot_password']['value'] ? 1 : 0, $meta)
				?>

				<?php
					Mfn_Builder_Admin::field( array(
						'id' => 'enable_goto_link',
						'type' => 'switch',
						'title' => $this->get_attributes['enable_goto_link']['title'],
						'options' => array(
							1 => 'Enable',
							0 => 'Disable'
						),
						'std' => '1',
						'desc' => $this->popup('enable_goto_link')
					), $this->options['enable_goto_link']['value'] ? 1 : 0, $meta)
				?>

				<?php wp_nonce_field('becustom_nonce') ?>
				<?php submit_button( __('Save changes', 'becustom') );  ?>
			</form>
		</div>
	</div>

</div>
