<?php
class Be_custom_branding extends Be_custom {
  const page_name = 'branding';

  public $options = array();
  public $theme_name = '';
  public $regex_betheme_muffin = array('/Betheme/','/Muffin/', '/be-/');
  public $regex_mfn_links = '/.+(https:\/\/(themes|support).muffingroup).*/';

  public function get_template() {
    include_once( plugin_dir_path( __DIR__ ) . 'becustom/templates/'.self::page_name.'.php' );
  }

  public function add_menu() {
    $this->page = add_submenu_page(
      'be_custom',
      null,
      null,
      'manage_options',
      'be_custom_'.self::page_name,
      array( $this, 'get_template')
    );

    add_action('admin_print_styles-'. $this->page, array( $this, 'enqueue' ));
    remove_submenu_page('be_custom', 'be_custom_'.self::page_name);
  }

  public function form_handler() {
    $actual_user_schema = $this->options;

    if(!empty($_POST) && check_admin_referer( 'becustom_nonce' )) {
      foreach($_POST as $key => $value) {
        $actual_user_schema[$key]['value'] = $value;
      }

      update_option( 'be_custom_'.self::page_name, $actual_user_schema);

      //reload, display new, insertecd values in inputs
      $this->options = $this->iterate_merge_array(self::page_name);

      //temp solution
      echo '<script>window.location.reload(true);</script>';
    } else{
      //
    }
  }

  /**
   * Appearance > Themes settings
   */


  function change_theme_overlay( $themes ) {
    if($this->options['replaced_theme_image']['value']){
      $themes[ $this->theme_name  ]['screenshot'][0] = $this->options['replaced_theme_image']['value'];
    }

    return $themes;
  }

  function change_theme_name( $themes ) {
    if($this->options['betheme_label']['value']){
      $themes[ $this->theme_name  ]['name'] = $this->options['betheme_label']['value'];
    }

    return $themes;
  }

  function change_theme_description( $themes ) {
    if($this->options['replaced_theme_desc']['value']){
      $themes[ $this->theme_name  ]['description'] = $this->options['replaced_theme_desc']['value'];
    }

    return $themes;
  }

  function change_theme_author( $themes ) {
    if($this->options['replaced_theme_author']['value']){
      $themes[ $this->theme_name  ]['author'] = $this->options['replaced_theme_author']['value'];
      $themes[ $this->theme_name  ]['authorAndUri'] = $this->options['replaced_theme_author']['value'];
    }

    return $themes;
  }

  function visibility_theme_version( $classes ) {
    $becustom_built_in_info = $this->iterate_merge_array('built_in_features')['disable_theme_version']['value'];

    if ($becustom_built_in_info) {
      $classes .= ' mfn-hide-version';
    }

    return $classes;
  }

  /*
  * Creating filters for branding
  */

  public function create_filters_loop() {
    foreach($this->options as $field){
      add_filter($field['filter_name'], array($this, 'create_filter_'.$field['filter_name']) );
    }
  }

  public function create_filter_betheme_label($default) {
    $new_value = $this->options['betheme_label']['value'];

    if($new_value){
      $default = $new_value;
    }

    return $default;
  }

  public function create_filter_betheme_dynamic_slug($default) {
    $slug = $this->options['betheme_url_slug']['value'];
    $slug = !empty($slug) ? $slug : 'be';

    $default_theme_slug = 'be';
    $default_theme_label = 'betheme';

    //places where label will be overwritten with slug, if changed by becustom
    return ($slug != $default_theme_slug) ? $slug : $default_theme_label;
  }

  public function create_filter_betheme_logo($default) {
    $new_value = $this->options['replaced_logo_url']['value'];

    if($new_value){
      $default = '<img class="betheme-custom-logo" src="'. $new_value .'" />';
    }

    return $default;
  }

  public function create_filter_betheme_image($default) {
    $new_value = $this->options['replaced_theme_image']['value'];

    if($new_value){
      $default = $new_value;
    }

    return $default;
  }

  public function create_filter_betheme_desc($default) {
    $new_value = $this->options['replaced_theme_desc']['value'];

    if($new_value){
      $default = $new_value;
    }

    return $default;
  }

  public function create_filter_betheme_author($default) {
    $new_value = $this->options['replaced_theme_author']['value'];

    if($new_value){
      $default = $new_value;
    }

    return $default;
  }

  public function create_filter_betheme_slug($default) {
    $new_value = $this->options['betheme_url_slug']['value'];

    if($new_value){
      $default = $new_value;
    }

    return $default;
  }

  public function create_filter_betheme_options_filed_options($field) {
    $actual_muffin_label = apply_filters('betheme_label', 'Muffin');

    foreach ($field as $options_key => $options_value ) {
      $field[$options_key] = preg_replace($this->regex_betheme_muffin, $actual_muffin_label, $options_value);
    }

    return $field;
  }

  public function create_filter_betheme_options_filed_title($default) {
    $actual_muffin_label = apply_filters('betheme_label', 'Muffin');
    $new_value = preg_replace($this->regex_betheme_muffin, $actual_muffin_label, $default);

    return $new_value;
  }

  public function create_filter_betheme_options_filed_desc($default) {
    $is_support_disabled = $this->iterate_merge_array('built_in_features')['disable_support_link']['value'];
    $new_slug = apply_filters('betheme_slug', 'be').'-';

    if ($is_support_disabled) {
      //if something is linked to support, remove it
      $default = preg_replace($this->regex_mfn_links, ' ', $default);
    }

    //for anchor links like be-options#responsive
    $default = preg_replace($this->regex_betheme_muffin, $new_slug, $default);

    return $default;
  }

  public function create_filter_betheme_logo_nohtml($default) {
    $new_value = $this->options['replaced_logo_url']['value'];

    if($new_value){
      $default = $new_value;
    }

    return $default;
  }

  public function __construct() {
    parent::__construct();
    //Paths to 'info' images
    $this->branding['betheme_label']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/default-betheme-text.png';
    $this->branding['replaced_logo_url']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/default-betheme-logo.png';
    $this->branding['replaced_theme_image']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/default-betheme-theme-image.png';
    $this->branding['replaced_theme_desc']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/betheme-description.png';
    $this->branding['replaced_theme_author']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/default-betheme-author-name.png';
    $this->branding['betheme_url_slug']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/betheme-friendly-url.png';

    add_action( 'admin_menu', array( $this, 'add_menu'));

    //values, iterated to check if there is no new attributes
    //some of them, are cached in database
    $this->options = $this->iterate_merge_array(self::page_name);

    //values straight from the php schema
    $this->get_attributes = $this->get_page_attributes(self::page_name);

    //Appearance > Themes and Version Visibility
    if(!WHITE_LABEL){
      $this->theme_name = get_stylesheet();
      add_filter( 'wp_prepare_themes_for_js', array( $this, 'change_theme_overlay' ));
      add_filter( 'wp_prepare_themes_for_js', array( $this, 'change_theme_name' ));
      add_filter( 'wp_prepare_themes_for_js', array( $this, 'change_theme_description' ));
      add_filter( 'wp_prepare_themes_for_js', array( $this, 'change_theme_author' ));

      add_filter( 'admin_body_class', array( $this, 'visibility_theme_version' ));

      add_action( 'load_textdomain', array($this, 'create_filters_loop'), 1);
    }
  }
}

new Be_custom_branding();
