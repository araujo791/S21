<!-- modal: template display conditions -->

<div class="mfn-modal has-footer modal-display-conditions">

	<div class="mfn-modalbox mfn-form mfn-form-verical mfn-shadow-1">

		<div class="modalbox-header">

			<div class="options-group">
				<div class="modalbox-title-group">
					<span class="modalbox-icon mfn-icon-shop"></span>
					<div class="modalbox-desc">
						<h4 class="modalbox-title"><?php esc_html_e('Display Conditions', 'mfn-opts'); ?></h4>
					</div>
				</div>
			</div>

			<div class="options-group">
				<a class="mfn-option-btn mfn-option-blank btn-large btn-modal-close" title="Close" href="#">
					<span class="mfn-icon mfn-icon-close"></span>
				</a>
			</div>

		</div>

		<div class="modalbox-content">
			<span class="mfn-icon display-conditions"></span>
			<h3><?php esc_html_e('Where Do You Want to Display Your Template?', 'mfn-opts'); ?></h3>
			<p><?php _e('Set the conditions that determine where your Template is used throughout your site.<br>For example, choose \'Entire Site\' to display the template across your site.', 'mfn-opts'); ?></p>

			<?php 
			$conditions = (array) json_decode( get_post_meta($this->post_id, 'mfn_template_conditions', true) );
			// echo '<pre>';
			// print_r($conditions);
			// echo '</pre>';
			?>

			<form id="tmpl-conditions-form">
			<div class="mfn-dynamic-form mfn-form">

				<?php

				/*echo '<pre>';
				print_r($archives);
				echo '</pre>';*/

				if( $this->template_type && in_array($this->template_type, array('single-product', 'shop-archive')) ):

				$cats = array();
				$tags = array();

				if (function_exists('is_woocommerce')) {
					$cats = get_terms( 'product_cat', array( 'hide_empty' => false, ) );
					//$tags = get_terms( 'product_tag', array( 'hide_empty' => false, ) );
					$tags = $wpdb->get_results( "SELECT tt.term_id, te.name FROM {$wpdb->prefix}term_taxonomy tt INNER JOIN {$wpdb->prefix}terms te ON tt.term_id = te.term_id WHERE tt.taxonomy = 'product_tag' Limit 150 " );
				}

				if( isset($conditions) && count($conditions) > 0){ $x = 0; foreach($conditions as $c=>$cond){ ?>
					<div class="mfn-df-row">
					<div class="df-row-inputs">
						<select name="mfn_template_conditions[<?php echo $x; ?>][rule]" class="mfn-form-control df-input df-input-rule <?php if($cond->rule == 'exclude'){ echo 'minus'; } ?>">
							<option <?php if($cond->rule == 'include'){ echo 'selected'; } ?> value="include"><?php esc_html_e('Include', 'mfn-opts'); ?></option>
							<option <?php if($cond->rule == 'exclude'){ echo 'selected'; } ?> value="exclude"><?php esc_html_e('Exclude', 'mfn-opts'); ?></option>
						</select>
						<select name="mfn_template_conditions[<?php echo $x; ?>][var]" class="mfn-form-control df-input df-input-var">
							<option <?php if($cond->var == 'shop'){ echo 'selected'; } ?> value="shop"><?php esc_html_e('Shop', 'mfn-opts'); ?></option>
							<option <?php if($cond->var == 'productcategory'){ echo 'selected'; } ?> value="productcategory"><?php esc_html_e('Product Category', 'mfn-opts'); ?></option>
							<option <?php if($cond->var == 'producttag'){ echo 'selected'; } ?> value="producttag"><?php esc_html_e('Product Tag', 'mfn-opts'); ?></option>
						</select>
						<select name="mfn_template_conditions[<?php echo $x; ?>][productcategory]" class="mfn-form-control df-input df-input-opt df-input-productcategory <?php if($cond->var == 'productcategory') {echo 'show';} ?>">
							<option value="all">All</option>
							<?php if(count($cats) > 0): foreach($cats as $cat){ ?>
							<option <?php if($cond->var != 'shop' && $cond->productcategory == $cat->term_id){ echo 'selected'; } ?> value="<?php echo $cat->term_id ?>"><?php echo $cat->name; ?></option>
							<?php } endif; ?>
						</select>
						<select name="mfn_template_conditions[<?php echo $x; ?>][producttag]" class="mfn-form-control df-input df-input-opt df-input-producttag <?php if($cond->var == 'producttag') {echo 'show';} ?>">
							<option value="all">All</option>
							<?php if(count($tags) > 0): foreach($tags as $tag){ ?>
							<option <?php if($cond->var != 'shop' && $cond->producttag == $tag->term_id){ echo 'selected'; } ?> value="<?php echo $tag->term_id ?>"><?php echo $tag->name; ?></option>
							<?php } endif; ?>
						</select>
					</div>
					<a class="mfn-option-btn mfn-option-blank btn-large df-remove" title="Close" href="#"><span class="mfn-icon mfn-icon-close"></span></a>
				</div>
				<?php $x++; }} ?>

				<div class="mfn-df-row clone df-type-woo">
					<div class="df-row-inputs">
						<select data-name="mfn_template_conditions[0][rule]" class="mfn-form-control df-input df-input-rule">
							<option value="include"><?php esc_html_e('Include', 'mfn-opts'); ?></option>
							<option value="exclude"><?php esc_html_e('Exclude', 'mfn-opts'); ?></option>
						</select>
						<select data-name="mfn_template_conditions[0][var]" class="mfn-form-control df-input df-input-var">
							<option value="shop"><?php esc_html_e('Shop', 'mfn-opts'); ?></option>
							<option value="productcategory"><?php esc_html_e('Product Category', 'mfn-opts'); ?></option>
							<option value="producttag"><?php esc_html_e('Product Tag', 'mfn-opts'); ?></option>
						</select>
						<select data-name="mfn_template_conditions[0][productcategory]" class="mfn-form-control df-input df-input-opt df-input-productcategory">
							<option value="all"><?php esc_html_e('All', 'mfn-opts'); ?></option>
							<?php if(count($cats) > 0): foreach($cats as $cat){ ?>
							<option value="<?php echo $cat->term_id ?>"><?php echo $cat->name; ?></option>
							<?php } endif; ?>
						</select>
						<select data-name="mfn_template_conditions[0][producttag]" class="mfn-form-control df-input df-input-opt df-input-producttag">
							<option value="all"><?php esc_html_e('All', 'mfn-opts'); ?></option>
							<?php if(count($tags) > 0): foreach($tags as $tag){ ?>
							<option value="<?php echo $tag->term_id ?>"><?php echo $tag->name; ?></option>
							<?php } endif; ?>
						</select>
					</div>
					<a class="mfn-option-btn mfn-option-blank btn-large df-remove" title="Close" href="#"><span class="mfn-icon mfn-icon-close"></span></a>
				</div>


				<?php elseif( $this->template_type && in_array($this->template_type, array('single-post', 'blog')) ):

				$cats = array();
				$tags = array();

				$cats = get_terms( 'category', array( 'hide_empty' => false, ) );
				$tags = get_terms( 'post_tag', array( 'hide_empty' => false, ) );

				if( !empty($conditions) && count($conditions) > 0 ){ $x = 0; foreach($conditions as $c=>$cond) { ?>
				<div class="mfn-df-row">
					<div class="df-row-inputs">
						<select name="mfn_template_conditions[<?php echo $x; ?>][rule]" class="mfn-form-control df-input df-input-rule <?php if($cond->rule == 'exclude'){ echo 'minus'; } ?>">
							<option <?php if($cond->rule == 'include'){ echo 'selected'; } ?> value="include"><?php esc_html_e('Include', 'mfn-opts'); ?></option>
							<option <?php if($cond->rule == 'exclude'){ echo 'selected'; } ?> value="exclude"><?php esc_html_e('Exclude', 'mfn-opts'); ?></option>
						</select>
						<select name="mfn_template_conditions[<?php echo $x; ?>][var]" class="mfn-form-control df-input df-input-var">
							<option <?php if($cond->var == 'all'){ echo 'selected'; } ?> value="all"><?php echo $this->template_type == 'blog' ? 'Blog' : 'All posts'; ?></option>
							<option <?php if($cond->var == 'category'){ echo 'selected'; } ?> value="category"><?php esc_html_e('Category', 'mfn-opts'); ?></option>
							<option <?php if($cond->var == 'post_tag'){ echo 'selected'; } ?> value="post_tag"><?php esc_html_e('Tag', 'mfn-opts'); ?></option>
						</select>
						<select name="mfn_template_conditions[<?php echo $x; ?>][category]" class="mfn-form-control df-input df-input-opt df-input-category <?php if($cond->var == 'category') {echo 'show';} ?>">
							<?php if(count($cats) > 0): foreach($cats as $cat){ ?>
							<option <?php if($cond->var == 'category' && $cond->category == $cat->term_id){ echo 'selected'; } ?> value="<?php echo $cat->term_id ?>"><?php echo $cat->name; ?></option>
							<?php } endif; ?>
						</select>
						<select name="mfn_template_conditions[<?php echo $x; ?>][post_tag]" class="mfn-form-control df-input df-input-opt df-input-post_tag <?php if($cond->var == 'post_tag') {echo 'show';} ?>">
							<?php if(count($tags) > 0): foreach($tags as $tag){ ?>
							<option <?php if($cond->var == 'post_tag' && $cond->post_tag == $tag->term_id){ echo 'selected'; } ?> value="<?php echo $tag->term_id ?>"><?php echo $tag->name; ?></option>
							<?php } endif; ?>
						</select>
					</div>
					<a class="mfn-option-btn mfn-option-blank btn-large df-remove" title="Close" href="#"><span class="mfn-icon mfn-icon-close"></span></a>
				</div>
				<?php $x++; }} ?>

				<div class="mfn-df-row clone">
					<div class="df-row-inputs">
						<select data-name="mfn_template_conditions[0][rule]" class="mfn-form-control df-input df-input-rule">
							<option value="include"><?php esc_html_e('Include', 'mfn-opts'); ?></option>
							<option value="exclude"><?php esc_html_e('Exclude', 'mfn-opts'); ?></option>
						</select>
						<select data-name="mfn_template_conditions[0][var]" class="mfn-form-control df-input df-input-var">
							<option value="all"><?php echo $this->template_type == 'blog' ? 'Blog' : 'All posts'; ?></option>
							<option value="category"><?php esc_html_e('Category', 'mfn-opts'); ?></option>
							<option value="post_tag"><?php esc_html_e('Tag', 'mfn-opts'); ?></option>
						</select>
						<select data-name="mfn_template_conditions[0][category]" class="mfn-form-control df-input df-input-opt df-input-category">
							<?php if(count($cats) > 0): foreach($cats as $cat){ ?>
							<option value="<?php echo $cat->term_id ?>"><?php echo $cat->name; ?></option>
							<?php } endif; ?>
						</select>
						<select data-name="mfn_template_conditions[0][post_tag]" class="mfn-form-control df-input df-input-opt df-input-post_tag">
							<?php if(count($tags) > 0): foreach($tags as $tag){ ?>
							<option value="<?php echo $tag->term_id ?>"><?php echo $tag->name; ?></option>
							<?php } endif; ?>
						</select>
					</div>
					<a class="mfn-option-btn mfn-option-blank btn-large df-remove" title="Close" href="#"><span class="mfn-icon mfn-icon-close"></span></a>
				</div>

				<?php elseif( $this->template_type && in_array($this->template_type, array('single-portfolio', 'portfolio')) ):

				$portfolio_cats = array();
				$portfolio_cats = get_terms( 'portfolio-types', array( 'hide_empty' => false, ) );

				if( !empty($conditions) && count($conditions) > 0 ){ $x = 0; foreach($conditions as $c=>$cond) { ?>
				<div class="mfn-df-row">
					<div class="df-row-inputs">
						<select name="mfn_template_conditions[<?php echo $x; ?>][rule]" class="mfn-form-control df-input df-input-rule <?php if($cond->rule == 'exclude'){ echo 'minus'; } ?>">
							<option <?php if($cond->rule == 'include'){ echo 'selected'; } ?> value="include"><?php esc_html_e('Include', 'mfn-opts'); ?></option>
							<option <?php if($cond->rule == 'exclude'){ echo 'selected'; } ?> value="exclude"><?php esc_html_e('Exclude', 'mfn-opts'); ?></option>
						</select>
						<select name="mfn_template_conditions[<?php echo $x; ?>][var]" class="mfn-form-control df-input df-input-var">
							<option <?php if($cond->var == 'all'){ echo 'selected'; } ?> value="all"><?php echo $this->template_type == 'portfolio' ? 'Portfolio' : 'All projects'; ?></option>
							<option <?php if($cond->var == 'portfolio-types'){ echo 'selected'; } ?> value="portfolio-types"><?php esc_html_e('Category', 'mfn-opts'); ?></option>
						</select>
						<select name="mfn_template_conditions[<?php echo $x; ?>][portfolio-types]" class="mfn-form-control df-input df-input-opt df-input-portfolio-types <?php if($cond->var == 'portfolio-types') {echo 'show';} ?>">
							<?php if(count($portfolio_cats) > 0): foreach($portfolio_cats as $pc){ ?>
							<option <?php if($cond->var == 'portfolio-types' && $cond->{'portfolio-types'} == $pc->term_id){ echo 'selected'; } ?> value="<?php echo $pc->term_id ?>"><?php echo $pc->name; ?></option>
							<?php } endif; ?>
						</select>
					</div>
					<a class="mfn-option-btn mfn-option-blank btn-large df-remove" title="Close" href="#"><span class="mfn-icon mfn-icon-close"></span></a>
				</div>
				<?php $x++; }} ?>

				<div class="mfn-df-row clone">
					<div class="df-row-inputs">
						<select data-name="mfn_template_conditions[0][rule]" class="mfn-form-control df-input df-input-rule">
							<option value="include"><?php esc_html_e('Include', 'mfn-opts'); ?></option>
							<option value="exclude"><?php esc_html_e('Exclude', 'mfn-opts'); ?></option>
						</select>
						<select data-name="mfn_template_conditions[0][var]" class="mfn-form-control df-input df-input-var">
							<option value="all"><?php echo $this->template_type == 'portfolio' ? 'Portfolio' : 'All projects'; ?></option>
							<option value="portfolio-types"><?php esc_html_e('Category', 'mfn-opts'); ?></option>
						</select>
						<select data-name="mfn_template_conditions[0][portfolio-types]" class="mfn-form-control df-input df-input-opt df-input-portfolio-types">
							<?php if(count($portfolio_cats) > 0): foreach($portfolio_cats as $pc){ ?>
							<option value="<?php echo $pc->term_id ?>"><?php echo $pc->name; ?></option>
							<?php } endif; ?>
						</select>
					</div>
					<a class="mfn-option-btn mfn-option-blank btn-large df-remove" title="Close" href="#"><span class="mfn-icon mfn-icon-close"></span></a>
				</div>










				<?php else: 

				$mfn_cond_terms = mfn_get_posttypes('tax');
				/*echo '<pre>';
				print_r($mfn_cond_terms);
				echo '</pre>';*/

				if( isset($conditions) && count($conditions) > 0){ $x = 0; foreach($conditions as $c=>$cond){ ?>
					<div class="mfn-df-row">
					<div class="df-row-inputs">
						<select name="mfn_template_conditions[<?php echo $x; ?>][rule]" class="mfn-form-control df-input df-input-rule <?php if($cond->rule == 'exclude'){ echo 'minus'; } ?>">
							<option <?php if($cond->rule == 'include'){ echo 'selected'; } ?> value="include"><?php esc_html_e('Include', 'mfn-opts'); ?></option>
							<option <?php if($cond->rule == 'exclude'){ echo 'selected'; } ?> value="exclude"><?php esc_html_e('Exclude', 'mfn-opts'); ?></option>
						</select>
						<select name="mfn_template_conditions[<?php echo $x; ?>][var]" class="mfn-form-control df-input df-input-var">
							<option <?php if($cond->var == 'everywhere'){ echo 'selected'; } ?> value="everywhere"><?php esc_html_e('Entire Site', 'mfn-opts'); ?></option>
							<option <?php if($cond->var == 'archives'){ echo 'selected'; } ?> value="archives"><?php esc_html_e('Archives', 'mfn-opts'); ?></option>
							<option <?php if($cond->var == 'singular'){ echo 'selected'; } ?> value="singular"><?php esc_html_e('Singular', 'mfn-opts'); ?></option>
						</select>
						<select name="mfn_template_conditions[<?php echo $x; ?>][archives]" class="mfn-form-control df-input df-input-opt df-input-archives <?php if($cond->var == 'archives') {echo 'show';} ?>">
							<?php if(count($mfn_cond_terms) > 0): foreach($mfn_cond_terms as $s=>$item){
								if( is_array($item) && $item['items'] ){
									echo '<optgroup label="'.$item['label'].'">';
									echo '<option '.( !empty($cond->archives) && $cond->archives == $s ? "selected" : null ).' value="'.$s.'">'.esc_html__('All', 'mfn-opts').'</option>';
									if( is_iterable($item['items']) ){
										foreach($item['items'] as $opt){
											echo '<option '.( !empty($cond->archives) && $cond->archives == $s.':'.$opt->id ? "selected" : null ).' value="'.$s.':'.$opt->id.'">'.$opt->name.'</option>';
										}
									}
									echo '</optgroup>';
								}elseif( !is_array($item) ){
									echo '<option '.( !empty($cond->archives) && $cond->archives == $s ? "selected" : null ).' value="'.$s.'">'.$item.'</option>';
								}
							} endif; ?>
						</select>
						<select name="mfn_template_conditions[<?php echo $x; ?>][singular]" class="mfn-form-control df-input df-input-opt df-input-singular <?php if($cond->var == 'singular') {echo 'show';} ?>">
							<?php 
							if(count($mfn_cond_terms) > 0): foreach($mfn_cond_terms as $s=>$item){
								if( is_array($item) ){
									echo '<optgroup label="'.$item['label'].'">';
									echo '<option '.( !empty($cond->singular) && $cond->singular == $s ? "selected" : null ).' value="'.$s.'">'.esc_html__('All', 'mfn-opts').'</option>';
									/*if( $s == 'page' ){
										echo '<option '.( !empty($cond->singular) && $cond->singular == "front-page" ? "selected" : null ).' value="front-page">Front page</option>';
									}*/
									if( is_array($item) && $item['items'] ){
										if( is_iterable($item['items']) ){
											foreach( $item['items'] as $opt){
												echo '<option '.( !empty($cond->singular) && $cond->singular == $s.':'.$opt->id ? "selected" : null ).' value="'.$s.':'.$opt->id.'">'.$opt->name.'</option>';
											}
										}
										
									}
									echo '</optgroup>';
								}else{
									echo '<option '.( !empty($cond->singular) && $cond->singular == $s ? "selected" : null ).' value="'.$s.'">'.$item.'</option>';
								}
							} endif; ?>
						</select>
					</div>
					<a class="mfn-option-btn mfn-option-blank btn-large df-remove" title="Close" href="#"><span class="mfn-icon mfn-icon-close"></span></a>
				</div>
				<?php $x++; }} ?>

				<div class="mfn-df-row clone df-type-tmpl-part">
					<div class="df-row-inputs">
						<select data-name="mfn_template_conditions[0][rule]" class="mfn-form-control df-input df-input-rule">
							<option value="include"><?php esc_html_e('Include', 'mfn-opts'); ?></option>
							<option value="exclude"><?php esc_html_e('Exclude', 'mfn-opts'); ?></option>
						</select>
						<select data-name="mfn_template_conditions[0][var]" class="mfn-form-control df-input df-input-var">
							<option value="everywhere"><?php esc_html_e('Entire Site', 'mfn-opts'); ?></option>
							<option value="archives"><?php esc_html_e('Archives', 'mfn-opts'); ?></option>
							<option value="singular"><?php esc_html_e('Singular', 'mfn-opts'); ?></option>
						</select>
						<select data-name="mfn_template_conditions[0][archives]" class="mfn-form-control df-input df-input-opt df-input-archives">
							<?php if(count($mfn_cond_terms) > 0): foreach($mfn_cond_terms as $s=>$item){
								if( is_array($item) && $item['items'] ){
									echo '<optgroup label="'.$item['label'].'">';
									echo '<option value="'.$s.'">'.esc_html__('All', 'mfn-opts').'</option>';
									if( is_iterable($item['items']) ){
										foreach($item['items'] as $opt){
											echo '<option value="'.$s.':'.$opt->id.'">'.$opt->name.'</option>';
										}
									}
									echo '</optgroup>';
								}elseif( !is_array($item) ){
									echo '<option value="'.$s.'">'.$item.'</option>';
								}
							} endif; ?>
						</select>
						<select data-name="mfn_template_conditions[0][singular]" class="mfn-form-control df-input df-input-opt df-input-singular">
							<?php 
							if(count($mfn_cond_terms) > 0): foreach($mfn_cond_terms as $s=>$item){
								if( is_array($item) ){
									echo '<optgroup label="'.$item['label'].'">';
									echo '<option value="'.$s.'">'.esc_html__('All', 'mfn-opts').'</option>';
									/*if( $s == 'page' ){
										echo '<option value="front-page">Front page</option>';
									}*/
									if( is_array($item) && $item['items'] ){
										if( is_iterable($item['items']) ){
											foreach( $item['items'] as $opt){
												echo '<option value="'.$s.':'.$opt->id.'">'.$opt->name.'</option>';
											}
										}
									}
									echo '</optgroup>';
								}else{
									echo '<option value="'.$s.'">'.$item.'</option>';
								}
							} endif; ?>
						</select>
					</div>
					<a class="mfn-option-btn mfn-option-blank btn-large df-remove" title="Close" href="#"><span class="mfn-icon mfn-icon-close"></span></a>
				</div>

				<?php endif; ?>
			</div>

			<a class="mfn-btn btn-icon-left  df-add-row" href="#"><span class="btn-wrapper"><span class="mfn-icon mfn-icon-add"></span><?php esc_html_e('Add condition', 'mfn-opts'); ?></span></a>
			</form>
		</div>


		<div class="modalbox-footer">
			<div class="options-group right">
				<a class="mfn-btn mfn-btn-blue btn-modal-save btn-save-changes" href="#"><span class="btn-wrapper"><?php esc_html_e('Save', 'mfn-opts'); ?></span></a>
				<a class="mfn-btn btn-modal-close" href="#"><span class="btn-wrapper"><?php esc_html_e('Cancel', 'mfn-opts'); ?></span></a>
			</div>
		</div>

	</div>

</div>
