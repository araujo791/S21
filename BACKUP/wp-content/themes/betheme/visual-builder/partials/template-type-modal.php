<div class="mfn-modal has-footer modal-template-type show">

	<div class="mfn-modalbox mfn-form mfn-form-verical mfn-shadow-1">

		<div class="modalbox-header">

			<div class="options-group">
				<div class="modalbox-title-group">
					<span class="modalbox-icon mfn-icon-settings"></span>
					<div class="modalbox-desc">
						<h4 class="modalbox-title"><?php esc_html_e('New template', 'mfn-opts'); ?></h4>
					</div>
				</div>
			</div>

			<div class="options-group">
				<a class="mfn-option-btn mfn-option-blank btn-large btn-modal-close" title="Close" href="edit.php?post_type=template">
					<span class="mfn-icon mfn-icon-close"></span>
				</a>
			</div>

		</div>

		<div class="modalbox-content">
			<h3><?php esc_html_e('Templates Will Make Your Work Smarter', 'mfn-opts'); ?></h3>
			<p><?php esc_html_e('Create various pieces of your site, and then combine them with one click to build the final layout. It’s that simple.', 'mfn-opts'); ?></p>

			<div class="template-type-form">
				<h4><?php esc_html_e('Choose Type Of Template', 'mfn-opts'); ?></h4>

				<?php
					$type = $this->getReferer();

					$mfn_post_types = array(
						'header' => esc_html__('Header', 'mfn-opts'),
						'footer' => esc_html__('Footer', 'mfn-opts'),
						'popup' => esc_html__('Popup', 'mfn-opts'),
						'megamenu' => esc_html__('Mega menu', 'mfn-opts'),
						'sidemenu' => esc_html__('Sidebar menu', 'mfn-opts'),
						'single-post' => esc_html__('Single post', 'mfn-opts'),
						'blog' => esc_html__('Blog', 'mfn-opts'),
						'single-portfolio' => esc_html__('Single portfolio', 'mfn-opts'),
						'portfolio' => esc_html__('Portfolio', 'mfn-opts'),
						'default' => esc_html__('Page template', 'mfn-opts'),
						'section' => esc_html__('Global section', 'mfn-opts'),
						'wrap' => esc_html__('Global wrap', 'mfn-opts'),
					);

					if(function_exists('is_woocommerce')){
						$mfn_post_types['single-product'] = esc_html__('Single product', 'mfn-opts');
						$mfn_post_types['shop-archive'] = esc_html__('Shop archive', 'mfn-opts');
					}
					
				?>

				<!-- input 1 -->
				<label class="form-label"><?php esc_html_e('Select the type of template you would like to create', 'mfn-opts'); ?></label>
				<select class="mfn-form-control select-template-type df-input">
					<?php foreach ($mfn_post_types as $m => $p) {
						echo '<option value="'.$m.'" '.selected( $type, $m ).' >'.$p.'</option>';
					} ?>
				</select>

				<!-- input 2 -->
				<label class="form-label"><?php esc_html_e('Name your template', 'mfn-opts'); ?></label>
				<input type="text" class="mfn-form-control input-template-type-name df-input" placeholder="Name">

			</div>
		</div>

		<div class="modalbox-footer">
			<div class="options-group right">
				<a class="mfn-btn mfn-btn-blue btn-modal-save btn-save-template-type" data-builder="<?php echo apply_filters('betheme_slug', 'mfn'); ?>" href="#"><span class="btn-wrapper"><?php esc_html_e('Create template', 'mfn-opts'); ?></span></a>
				<a class="mfn-btn btn-modal-close" href="edit.php?post_type=template"><span class="btn-wrapper"><?php esc_html_e('Cancel', 'mfn-opts'); ?></span></a>
			</div>
		</div>

	</div>

</div>
