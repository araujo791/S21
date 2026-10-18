<?php

// 1. from product
// 2. by conditions (cat, tag)
// 3. from theme options by default

global $mfn_global;

if( ( empty($_GET['visual']) || !empty($_GET['mfn-template-id']) ) && !empty( $mfn_global['single_product'] ) && is_numeric( $mfn_global['single_product'] ) && get_post_type( $mfn_global['single_product'] ) == 'template' ){

	global $product;

	$classes = ['mfn-single-product-tmpl-wrapper'];

	if( !empty( get_post_meta(get_the_ID(), '_sold_individually', true) ) && get_post_meta(get_the_ID(), '_sold_individually', true) == 'yes' ){
		$classes[] = 'sold-individually';
	}

	if( method_exists($product, 'get_stock_quantity') ){
		$product_quantity = $product->get_stock_quantity();
		if( 1 === $product_quantity ){
			$classes[] = 'quantity-one';
		}
	}
	
	echo '<div class="'. implode(' ', wc_get_product_class( $classes, get_the_ID() )) .'">';

		echo '<div class="section_wrapper no-bebuilder-section clearfix">';
			do_action( 'woocommerce_before_single_product' );
		echo '</div>';

		$mfn_builder = new Mfn_Builder_Front( $mfn_global['single_product'] );
		$mfn_builder->show();

		echo '<div class="section_wrapper no-bebuilder-section clearfix">';
			do_action('woocommerce_after_single_product');
		echo '</div>';

	echo '</div>';

}else{

	echo '<div class="section section_product_before_tabs">';
		echo '<div class="section_wrapper no-bebuilder-section clearfix">';
			woocommerce_content();
		echo '</div>';
	echo '</div>';

}

?>
