<?php
if( ! defined( 'ABSPATH' ) ){
	exit; // Exit if accessed directly
}

class Mfn_Helper {

	/**
	 * Initialises and connects the WordPress Filesystem
	 */

	public static function filesystem(){

		global $wp_filesystem;

		if( ! defined( 'FS_METHOD' ) ){
			define( 'FS_METHOD', 'direct' );
		}

		if( ! defined( 'FS_CHMOD_DIR' ) ){
			define( 'FS_CHMOD_DIR', ( 0755 & ~ umask() ) );
		}

		if( ! defined( 'FS_CHMOD_FILE' ) ){
			define( 'FS_CHMOD_FILE', ( 0644 & ~ umask() ) );
		}

		if( empty( $wp_filesystem ) ){
			require_once wp_normalize_path( ABSPATH .'/wp-admin/includes/file.php' );
		}

		WP_Filesystem();

		return $wp_filesystem;
	}

	/**
	 * Prepare local styles and fonts before update
	 */

	public static function preparePostUpdate($object, $post_id = false, $key = false) {
		$return = array();
		$return['custom'] = array();
		$return['global'] = array();
		$return['tablet'] = array();
		$return['laptop'] = array();
		$return['mobile'] = array();
		$return['query_modifiers'] = array();
		$return['fonts'] = array();
		$return['sidemenus'] = array();

		$additional_css = array(

		    'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-header-tmpl-menu-sidebar .mfn-header-menu li .mfn-submenu li a:justify-content' => array(
		        'new_id' 	=> 'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-header-tmpl-menu-sidebar .mfn-header-menu li .mfn-submenu li a:text-align',
		        'rewrites'  => array(
		            'flex-start' => 'left',
		            'flex-end' => 'right',
		            'center' => 'center',
		        )
		    ),

		    'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-header-tmpl-menu-sidebar .mfn-header-menu li .mfn-submenu li a:justify-content_tablet' => array(
		        'new_id' 	=> 'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-header-tmpl-menu-sidebar .mfn-header-menu li .mfn-submenu li a:text-align_tablet',
		        'rewrites'  => array(
		            'flex-start' => 'left',
		            'flex-end' => 'right',
		            'center' => 'center',
		        )
		    ),

		    'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-header-tmpl-menu-sidebar .mfn-header-menu li .mfn-submenu li a:justify-content_laptop' => array(
		        'new_id' 	=> 'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-header-tmpl-menu-sidebar .mfn-header-menu li .mfn-submenu li a:text-align_laptop',
		        'rewrites'  => array(
		            'flex-start' => 'left',
		            'flex-end' => 'right',
		            'center' => 'center',
		        )
		    ),

		    'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-header-tmpl-menu-sidebar .mfn-header-menu li .mfn-submenu li a:justify-content_mobile' => array(
		        'new_id' 	=> 'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-header-tmpl-menu-sidebar .mfn-header-menu li .mfn-submenu li a:text-align_mobile',
		        'rewrites'  => array(
		            'flex-start' => 'left',
		            'flex-end' => 'right',
		            'center' => 'center',
		        )
		    ),

		    'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-banner-box .banner-wrapper:text-align' => array(
		        'new_id' 	=> 'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-banner-box .banner-wrapper:align-items',
		        'rewrites'  => array(
		            'left' => 'flex-start',
		            'right' => 'flex-end',
		            'center' => 'center',
		        )
		    ),

		    'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-banner-box .banner-wrapper:text-align_laptop' => array(
		        'new_id' 	=> 'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-banner-box .banner-wrapper:align-items_laptop',
		        'rewrites'  => array(
		            'left' => 'flex-start',
		            'right' => 'flex-end',
		            'center' => 'center',
		        )
		    ),

		    'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-banner-box .banner-wrapper:text-align_tablet' => array(
		        'new_id' 	=> 'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-banner-box .banner-wrapper:align-items_tablet',
		        'rewrites'  => array(
		            'left' => 'flex-start',
		            'right' => 'flex-end',
		            'center' => 'center',
		        )
		    ),

		    'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-banner-box .banner-wrapper:text-align_mobile' => array(
		        'new_id' 	=> 'style:.mcb-section .mcb-wrap .mcb-item-mfnuidelement .mfn-banner-box .banner-wrapper:align-items_mobile',
		        'rewrites'  => array(
		            'left' => 'flex-start',
		            'right' => 'flex-end',
		            'center' => 'center',
		        )
		    ),

		);

		$tmpl_type = get_post_meta($post_id, 'mfn_template_type', true);

		$meta_key = $key ? $key : 'mfn-page-local-style';

		if( !empty($object) && count($object) > 0 ) {
			foreach ($object as $i => $item) {

				if( !empty($item['attr']) ) {

					// fonts
					if( !empty($item['attr']['used_fonts']) ) {
						$fonts_arr = explode(',', $item['attr']['used_fonts']);
						$return['fonts'] = array_unique(array_merge($return['fonts'],$fonts_arr));
					}

					// query modifiers
					if( isset($item['jsclass']) && in_array($item['jsclass'], array('wrap', 'section')) && !empty($item['attr']['type']) && $item['attr']['type'] == 'query' ) {
						if( !empty($item['attr']['query_post_per_page']) ) $return['query_modifiers']['posts_per_page'] = $item['attr']['query_post_per_page'];
						if( !empty($item['attr']['query_post_order']) ) $return['query_modifiers']['order'] = $item['attr']['query_post_order'];
					}

					if( isset($item['jsclass']) && in_array($item['jsclass'], array('blog')) && $tmpl_type == 'blog' ) {
						if( !empty($item['attr']['count']) ) $return['query_modifiers']['posts_per_page'] = $item['attr']['count'];
						if( !empty($item['attr']['orderby']) ) $return['query_modifiers']['orderby'] = $item['attr']['orderby'];
						if( !empty($item['attr']['order']) ) $return['query_modifiers']['order'] = $item['attr']['order'];
					}

					if( !empty($item['attr']['sidebar_type']) ) {
						$return['sidemenus'][] = $item['attr']['sidebar_type'];
					}

					// shop products
					if( !empty($item['jsclass']) && $item['jsclass'] == 'shop_products' ) {
						if( !empty($item['attr']['products']) ) update_post_meta( $post_id, 'mfn_template_perpage', $item['attr']['products'] );

						if( !empty($item['attr']['shop-list-active-filters']) ) { update_post_meta( $post_id, 'mfn-shop-list-active-filters', 'visible' ); }else{ update_post_meta( $post_id, 'mfn-shop-list-active-filters', 'hidden' ); }
						if( !empty($item['attr']['shop-list-perpage']) ) { update_post_meta( $post_id, 'mfn-shop-list-perpage', 'visible' ); }else{ update_post_meta( $post_id, 'mfn-shop-list-perpage', 'hidden' ); }
						if( !empty($item['attr']['shop-list-layout']) ) { update_post_meta( $post_id, 'mfn-shop-list-layout', 'visible' ); }else{ update_post_meta( $post_id, 'mfn-shop-list-layout', 'hidden' ); }
						if( !empty($item['attr']['shop-list-sorting']) ) { update_post_meta( $post_id, 'mfn-shop-list-sorting', 'visible' ); }else{ update_post_meta( $post_id, 'mfn-shop-list-sorting', 'hidden' ); }
						if( !empty($item['attr']['shop-list-results-count']) ) { update_post_meta( $post_id, 'mfn-shop-list-results-count', 'visible' ); }else{ update_post_meta( $post_id, 'mfn-shop-list-results-count', 'hidden' ); }

						if( !empty($item['attr']['ordering']) ) { update_post_meta( $post_id, 'mfn_default_order', $item['attr']['ordering'] ); }else{ delete_post_meta( $post_id, 'mfn_default_order' ); }

					}

					// cart button label
					if( !empty($item['jsclass']) && $item['jsclass'] == 'product_cart_button' && !empty($item['attr']['cart_button_text']) ) {
						update_post_meta( $post_id, 'mfn_cart_button', $item['attr']['cart_button_text'] );
					}

					foreach ($item['attr'] as $a => $attr) {

						if( strpos( $a, 'style:' ) !== false ) {

							if( is_array($attr) && !empty($attr) ) {
								foreach ($attr as $s => $style) {

									if( strpos( $a, 'gradient' ) !== false && $s != 'string' ) continue;
									if( strpos( $a, ':filter' ) !== false && $s != 'string' ) continue;
									if( strpos( $a, ':backdrop-filter' ) !== false && $s != 'string' ) continue;

									if( strpos( $s, 'font-family' ) !== false && !empty($style) && !in_array($style, $return['fonts']) ){
										$return['fonts'][] = $style;
										$style = "'".$style."'";
									}

									if( strpos( $a, '_tablet' ) !== false || strpos( $s, '_tablet' ) !== false){
										$return['tablet'] = array_merge_recursive($return['tablet'], self::mfnLocalStyle($a.'_'.$s, $style, $item['uid'], $post_id));
									}elseif( strpos( $a, '_mobile' ) !== false || strpos( $s, '_mobile' ) !== false){
										$return['mobile'] = array_merge_recursive($return['mobile'], self::mfnLocalStyle($a.'_'.$s, $style, $item['uid'], $post_id));
									}elseif( strpos( $a, '_laptop' ) !== false || strpos( $s, '_laptop' ) !== false){
										$return['laptop'] = array_merge_recursive($return['laptop'], self::mfnLocalStyle($a.'_'.$s, $style, $item['uid'], $post_id));
									}elseif( strpos( $a, '_custom' ) !== false || strpos( $s, '_custom' ) !== false ){
	  									$return['custom'] = array_merge_recursive($return['custom'], self::mfnLocalStyle($a.'_'.$s, $style, $item['uid'], $post_id));
	  								}else{
										$return['global'] = array_merge_recursive($return['global'], self::mfnLocalStyle($a.'_'.$s, $style, $item['uid'], $post_id));
									}
								}
							}else{
								if(strpos( $a, '_tablet' ) !== false){
									$return['tablet'] = array_merge_recursive($return['tablet'], self::mfnLocalStyle($a, $attr, $item['uid'], $post_id));
									if( !empty($additional_css[$a]) && !empty($additional_css[$a]['rewrites'][$attr]) ) $return['tablet'] = array_merge_recursive($return['tablet'], self::mfnLocalStyle($additional_css[$a]['new_id'], $additional_css[$a]['rewrites'][$attr], $item['uid'], $post_id));
								}elseif(strpos( $a, '_mobile' ) !== false){
									$return['mobile'] = array_merge_recursive($return['mobile'], self::mfnLocalStyle($a, $attr, $item['uid'], $post_id));
									if( !empty($additional_css[$a]) && !empty($additional_css[$a]['rewrites'][$attr]) ) $return['mobile'] = array_merge_recursive($return['mobile'], self::mfnLocalStyle($additional_css[$a]['new_id'], $additional_css[$a]['rewrites'][$attr], $item['uid'], $post_id));
								}elseif(strpos( $a, '_laptop' ) !== false){
									$return['laptop'] = array_merge_recursive($return['laptop'], self::mfnLocalStyle($a, $attr, $item['uid'], $post_id));
									if( !empty($additional_css[$a]) && !empty($additional_css[$a]['rewrites'][$attr]) ) $return['laptop'] = array_merge_recursive($return['laptop'], self::mfnLocalStyle($additional_css[$a]['new_id'], $additional_css[$a]['rewrites'][$attr], $item['uid'], $post_id));
								}elseif(strpos( $a, '_custom' ) !== false && strpos( $a, '_custom_' ) === false){
	  								$return['custom'] = array_merge_recursive($return['custom'], self::mfnLocalStyle($a, $attr, $item['uid'], $post_id));
	  							}else{
									$return['global'] = array_merge_recursive($return['global'], self::mfnLocalStyle($a, $attr, $item['uid'], $post_id));
									if( !empty($additional_css[$a]) && !empty($additional_css[$a]['rewrites'][$attr]) ) $return['global'] = array_merge_recursive($return['global'], self::mfnLocalStyle($additional_css[$a]['new_id'], $additional_css[$a]['rewrites'][$attr], $item['uid'], $post_id));
								}

							}

						}
					}
				}
			}
		}

		if( !empty($return['fonts']) && count($return['fonts']) > 0 ){
			update_post_meta( $post_id, 'mfn-page-fonts', json_encode($return['fonts']) );
		}else{
			delete_post_meta( $post_id, 'mfn-page-fonts' );
		}

		if( !empty($return['sidemenus']) && count($return['sidemenus']) > 0 ){
			update_post_meta( $post_id, 'mfn-template-sidemenu', json_encode( $return['sidemenus']) );
		}else{
			delete_post_meta( $post_id, 'mfn-template-sidemenu' );
		}

		if( get_post_type($post_id) == 'template' && in_array($tmpl_type, array('blog', 'portfolio')) ){
			if(!empty($return['query_modifiers'])){
				update_post_meta( $post_id, 'mfn-query-modifiers', json_encode( array_unique($return['query_modifiers'])) );
			}else{
				delete_post_meta( $post_id, 'mfn-query-modifiers' );
			}
		}

		update_post_meta( $post_id, $meta_key, json_encode($return) );

		$preview = $meta_key == 'mfn-builder-preview-local-style' ? true : false;

		Mfn_Helper::generate_css($return, $post_id, $preview);

		return $return;

	}

	/**
	 * Local style
	 */

	public static function mfnLocalStyle($sel, $val, $uid, $post_id = false) {

		if( empty($val) || $val == 'cover-ultrawide' || $val == 'custom' ) {
			return array();
		}

		$style_arr = array();

		$style_sel = explode(':', $sel);
		array_shift( $style_sel );

		$selector = $style_sel[0];

		if( $uid ){
			$selector = str_replace('mfnuidelement', $uid, $style_sel[0]);

			$selector = str_replace('mcb-section-inner', 'mcb-section-inner-'.$uid, $selector);
			$selector = str_replace('section_wrapper', 'mcb-section-inner-'.$uid, $selector);
			$selector = str_replace('mcb-wrap-inner', 'mcb-wrap-inner-'.$uid, $selector);
			$selector = str_replace('mcb-column-inner', 'mcb-column-inner-'.$uid, $selector);
		}

		$style_name = $style_sel[1];

		$values_prefixes = array(
			'flex' => '0 0 ',
			'flex_tablet' => '0 0 ',
			'flex_laptop' => '0 0 ',
			'flex_mobile' => '0 0 ',
			'background-image' => 'url(',
			'background-image_tablet' => 'url(',
			'background-image_laptop' => 'url(',
			'background-image_mobile' => 'url(',
			'-webkit-mask-image' => 'url(',
			'transformtranslatex' => 'translateX(',
			'transformtranslatey' => 'translateY(',
			'transform_string' => 'matrix(',
		);

		$values_postfixes = array(
			'background-image' => ')',
			'background-image_tablet' => ')',
			'background-image_laptop' => ')',
			'background-image_mobile' => ')',
			'-webkit-mask-image' => ')',
			'transformtranslatex' => ')',
			'transformtranslatey' => ')',
			'transform_string' => 'deg)'
		);

		$selector = str_replace('|', ':', $selector);

		$style_name = str_replace(array('_laptop', '_mobile', '_tablet', 'typography_', 'translatex', 'translatey', '_v2'), '', $style_name);
		$style_name = str_replace(array('_'), '-', $style_name);

		$style_value = str_replace('gradient-string', 'background-image', $style_name).':';
		$style_value = str_replace('filter-string', 'filter', $style_value);
		$style_value = str_replace('transform-string', 'transform', $style_value);

		if( !empty($values_prefixes[$style_sel[1]]) && $val != 'none' ){
			$style_value .= $values_prefixes[$style_sel[1]];
		}

		if ( $style_sel[1] === 'transform_string' ) {
			$val = preg_replace("/(\,+)(?!.*,)/", ") rotate(", $val);
		}

		$style_value .= $val;

		if( !empty($values_postfixes[$style_sel[1]]) && $val != 'none' ){
			$style_value .= $values_postfixes[$style_sel[1]];
		}

		if( strpos( $val, '{featured_image' ) !== false ) $style_value = 'background-image: var(--mfn-featured-image)';

		$style_value .= ';';

		$style_arr[$selector] = $style_value;
		return $style_arr;
	}

	public static function generate_css($mfn_styles, $post_id, $preview = false){

	  	$wp_filesystem = self::filesystem();

		$upload_dir = wp_upload_dir();
		$path_be = wp_normalize_path( $upload_dir['basedir'] .'/betheme' );
		$path_css = wp_normalize_path( $path_be .'/css' );

		if( $preview ){
			$path = wp_normalize_path( $path_css .'/post-'.$post_id.'-preview.css' );
		}else{
			$path = wp_normalize_path( $path_css .'/post-'.$post_id.'.css' );
		}

		if( ! file_exists( $path_be ) ){
			wp_mkdir_p( $path_be );
		}

		if( ! file_exists( $path_css ) ){
			wp_mkdir_p( $path_css );
		}

		$css = "";

		if( !empty($mfn_styles['global']) ){
			foreach($mfn_styles['global'] as $sel=>$st){
				if(is_array($st)){
					$css .= $sel.'{';
					foreach($st as $style){
						$css .= $style;
					}
					$css .= '}';
				}else{
					$css .= $sel.'{'.$st.'}';
				}
			}
		}

		if( !empty($mfn_styles['laptop']) ){
			$css .= '@media(max-width: 1440px){';
			foreach($mfn_styles['laptop'] as $sel=>$st){
				if(is_array($st)){
					$css .= $sel.'{';
					foreach($st as $style){
						$css .= $style;
					}
					$css .= '}';
				}else{
					$css .= $sel.'{'.$st.'}';
				}
			}
			$css .= '}';
		}

		if( !empty($mfn_styles['tablet']) ){
			$css .= '@media(max-width: 959px){';
			foreach($mfn_styles['tablet'] as $sel=>$st){
				if(is_array($st)){
					$css .= $sel.'{';
					foreach($st as $style){
						$css .= $style;
					}
					$css .= '}';
				}else{
					$css .= $sel.'{'.$st.'}';
				}
			}
			$css .= '}';
		}

		if( !empty($mfn_styles['mobile']) ){
			$css .= '@media(max-width: 767px){';
			foreach($mfn_styles['mobile'] as $sel=>$st){
				if(is_array($st)){
					$css .= $sel.'{';
					foreach($st as $style){
						$css .= $style;
					}
					$css .= '}';
				}else{
					$css .= $sel.'{'.$st.'}';
				}
			}
			$css .= '}';
		}

		if( !empty($mfn_styles['custom']) ){
			foreach($mfn_styles['custom'] as $sel=>$st){

				if(is_array($st)){
					foreach($st as $style){
						$mq = str_replace( array('show-under-custom', 'hide-under-custom', ':', ';'), '', $style );
						if( strpos( $style, 'hide-under' ) !== false ){
							$css .= '@media(max-width: '.$mq.'){ '.$sel.'{display: none;}}';
						}else if( strpos( $style, 'show-under' ) !== false ){
							$css .= $sel.'{display: none;}';
							$css .= '@media(max-width: '.$mq.'){ '.$sel.'{display: block;}}';
						}
					}
				}else{
					$mq = str_replace( array('show-under-custom', 'hide-under-custom', ':', ';'), '', $st );
					if( strpos( $st, 'hide-under' ) !== false ){
						$css .= '@media(max-width: '.$mq.'){ '.$sel.'{display: none;}}';
					}else if( strpos( $st, 'show-under' ) !== false ){
						$css .= $sel.'{display: none;}';
						$css .= '@media(max-width: '.$mq.'){ '.$sel.'{display: block;}}';
					}
				}


			}
		}

		//echo $css;
		$wp_filesystem->put_contents( $path, $css, FS_CHMOD_FILE );

	}

	public static function generate_bebuilder_items(){

		$bebuilder_access = apply_filters('bebuilder_access', false);
		if( !$bebuilder_access ) return false;

		MfnVisualBuilder::removeBeDataFile();
		$bepath = MfnVisualBuilder::bebuilderFilePath();

		$mfnVidualClass = new MfnVisualBuilder();
		$beitems = $mfnVidualClass->fieldsToJS();

		$wp_filesystem = self::filesystem();
		$folder_path = get_template_directory().'/visual-builder/assets/js/forms';
		if( ! file_exists( $folder_path ) ) wp_mkdir_p( $folder_path );
		$path = wp_normalize_path( $bepath );
		$make = $wp_filesystem->put_contents( $path, $beitems, FS_CHMOD_FILE );
		update_option('betheme_form_uid', Mfn_Builder_Helper::unique_ID());
		return $make;
	}

	/**
	 * Registration modal
	 */

	public static function the_modal_register(){

		?>

			<div class="mfn-register-now">
				<div class="inner-content">
					<div class="be">
						<img class="be-logo" src="<?php echo get_theme_file_uri( 'muffin-options/svg/others/be-gradient.svg' ); ?>" alt="Be">
					</div>
					<div class="info">
                        <span class="mfn-register-now-icon"></span>
						<h4>Please register the license<br />to get the access to Muffin Options</h4>
						<p class="">This page reload is required after theme registration</p>
						<a class="mfn-btn mfn-btn-green btn-large" href="admin.php?page=betheme" target="_blank"><span class="btn-wrapper">Register now</span></a>
					</div>
				</div>
			</div>

		<?php

	}

	/**
	 * Cache string
	 */

	public static function get_cache_text()
	{
		$content = '
# BEGIN BETHEME';

		$content .= '
<IfModule mod_expires.c>
ExpiresActive On

# Images
ExpiresByType image/jpeg "access plus 1 year"
ExpiresByType image/gif "access plus 1 year"
ExpiresByType image/png "access plus 1 year"
ExpiresByType image/webp "access plus 1 year"
ExpiresByType image/svg+xml "access plus 1 year"
ExpiresByType image/x-icon "access plus 1 year"

# Video
ExpiresByType video/webm "access plus 1 year"
ExpiresByType video/mp4 "access plus 1 year"
ExpiresByType video/mpeg "access plus 1 year"

# Fonts
ExpiresByType font/ttf "access plus 1 year"
ExpiresByType font/otf "access plus 1 year"
ExpiresByType font/woff "access plus 1 year"
ExpiresByType font/woff2 "access plus 1 year"
ExpiresByType application/font-woff "access plus 1 year"

# CSS, JavaScript
ExpiresByType text/css "access plus 6 months"
ExpiresByType text/javascript "access plus 6 months"
ExpiresByType application/javascript "access plus 6 months"

# Others
ExpiresByType application/pdf "access plus 6 months"
ExpiresByType image/vnd.microsoft.icon "access plus 1 year"

ExpiresDefault "access 1 month"

</IfModule>
';

		$content .= '# END BETHEME';
		return $content;
	}

}
