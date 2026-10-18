<?php  

if( ! defined( 'ABSPATH' ) ) exit; // Exit if accessed directly

class MfnConditionalLogic {

	public $id = false;

	public function verify( $conditions = false ) {

		if( !$conditions || empty($conditions) ) return true;

		$helper = array();
		$return = false;

		$this->id = false;

		if( !empty(Mfn_Builder_Front::$item_id) ) {
			$this->id = Mfn_Builder_Front::$item_id;
		}else if( is_singular() ){
			$this->id = get_the_ID();
		}

		foreach($conditions as $c=>$cond){
			foreach( $cond as $r=>$row ){

				$fun_name = 'is_'.$row['key'];
				$check = $this->$fun_name();

				/*echo '<pre>';
				print_r($check);
				echo '</pre>';*/

				$val = is_array($row['value']) ? $row['value']['id'] : $row['value'];

				if( (is_array($check) && in_array($val, $check)) || $check == $val ){
					$helper[$c][] = $check && $row['var'] == 'is' ? 1 : 0;
				}else{
					$helper[$c][] = $row['var'] == 'is' ? 0 : 1;
				}

			}
		}

		if( !empty($helper) ){
			foreach( $helper as $h ){
				if( (is_array($h) && count(array_unique($h)) == 1 && array_unique($h)[0] == 1) || $h == 1 ){
					$return = true;
				}
			}
		}

		/*echo '<pre>';
		print_r($helper);
		echo '</pre>';*/

		return $return;

	}

	public function is_post_type() {
		if( $this->id ){
			return get_post_type($this->id);
		}

		return false;
	}

	public function is_post_taxonomy() {
		if( !$this->id ) return false;

		$return = array();

		$post_type = get_post_type($this->id);

		$data = array(
			'page' => array(),
			'post' => array('category', 'post_tag'),
			'portfolio' => array('portfolio-types'),
			'offer' => array('offer-types'),
			'slide' => array('slide-types'),
		);

		if( function_exists('is_woocommerce') ) {
			$data['product'] = array('product_cat', 'product_tag');
		}

		$post_type_terms = $data[$post_type];

		if( !empty($post_type_terms) ){
			foreach($post_type_terms as $tax){
				$terms = get_the_terms( get_the_ID(), $tax );

				if ( ! empty( $terms ) ) {
					foreach($terms as $term){
						$return[] = $term->term_id;
					}
				}
			}
		}

		return $return;
	}

	public function is_post() {
		return $this->id;
	}

	public function is_post_type_archive() {
		
		if( is_singular() ) return false;

		if( is_home() || is_post_type_archive('post') || is_category() ) {
			return 'post';
		}else if( is_post_type_archive('portfolio') || is_tax( 'portfolio-types' ) || ( is_page() && get_the_ID() == mfn_opts_get('portfolio-page') ) ) {
			return 'portfolio';
		}else if( function_exists('is_woocommerce') && ( is_shop() || is_product_category() || is_product_tag() ) ) {
			return 'product';
		}

		return false;
	}

	public function is_archive_category() {
		$qo = get_queried_object();

		if( !empty($qo->term_id) ){
			return $qo->term_id;
		}

		return false;
	}

	public function is_login_status() {
		if(is_user_logged_in()){
			return 'logged_in';
		}else{
			return 'non_logged';
		}
	}

	public function is_user_role() {
		if( !is_user_logged_in() ) return false;

		$user = wp_get_current_user();
 
    	$roles = ( array ) $user->roles;

		return $roles;
	}

	public function is_part_of_the_week() {
		$parts = array();

		if(date('D') == 'Sat' || date('D') == 'Sun') {
			$parts[] = 'weekend';
			if(date('D') == 'Sat') $parts[] = 'saturday';
			if(date('D') == 'Sun') $parts[] = 'sunday';
		}else{
			$parts[] = 'monday-friday';

			if(date('D') == 'Mon') $parts[] = 'monday';
			if(date('D') == 'Tue') $parts[] = 'tuesday';
			if(date('D') == 'Wed') $parts[] = 'wednesday';
			if(date('D') == 'Thu') $parts[] = 'thursday';
			if(date('D') == 'Fri') $parts[] = 'friday';

		}

		return $parts;
	}

	public function is_date() {
		return date('Y-m-d');
	}

	public function is_featured_image() {
		if( !$this->id ) return false;

		if( has_post_thumbnail() ){
			return 'set';
		}else{
			return 'not-set';
		}
	}

	public function is_excerpt() {
		if( !$this->id ) return false;

		if( has_excerpt( $this->id ) ){
			return 'set';
		}else{
			return 'not-set';
		}
	}

}


?>