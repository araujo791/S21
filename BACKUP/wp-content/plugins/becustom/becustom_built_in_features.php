<?php
class Be_custom_built_in_features extends Be_custom {
  const page_name = 'built_in_features';
  public $options = array();

  public $theme_name = '';

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

  function disable_theme_update_notification( $value ) {
    if ( isset( $value ) && is_object( $value ) && $this->options['disable_theme_update']['value']) {
      unset( $value->response[ $this->theme_name  ] );
    }
    return $value;
  }

  public function form_handler() {
    $actual_user_schema = $this->options;

    if(!empty($_POST) && check_admin_referer( 'becustom_nonce' )) {

      foreach($_POST as $key => $value) {
        $actual_user_schema[$key]['value'] = filter_var($value, FILTER_VALIDATE_BOOLEAN);
      }

      update_option( 'be_custom_'.self::page_name, $actual_user_schema);

      //reload, display new, insertecd values in inputs
      $this->options = $this->iterate_merge_array(self::page_name);
    } else{
      //
    }
  }

  /*
  * Creating filters for branding
  */

  public function create_filters_loop() {
    foreach($this->options as $field){
      add_filter($field['filter_name'], array($this, 'create_filter_'.$field['filter_name']) );
    }
  }

  public function create_filter_betheme_disable_theme_version($default) {
    $new_value = $this->options['disable_theme_version']['value'];

    if($new_value){
      //we have to hide the version theme, so provide empty string
      $default = '';
    }

    return $default;
  }

  public function create_filter_betheme_disable_support($default) {
    $new_value = $this->options['disable_support_link']['value'];

    if($new_value){
      $default = $new_value;
    }

    return $default;
  }


  public function create_filter_betheme_disable_changelog($default) {
    $new_value = $this->options['disable_changelog_link']['value'];

    if($new_value){
      $default = $new_value;
    }

    return $default;
  }

  public function create_filter_betheme_disable_theme_update($default) {
    $are_updates_disabled = $this->options['disable_theme_update']['value'];

    if($are_updates_disabled){
      $default = MFN_THEME_VERSION;
    }

    return $default;
  }

  public function create_filter_betheme_disable_advanced($default) {
    $new_value = $this->options['disable_advanced_tab']['value'];

    if($new_value){
      $default = $new_value;
    }

    return $default;
  }

  public function create_filter_betheme_disable_hooks($default) {
    $new_value = $this->options['disable_hooks_tab']['value'];

    if($new_value){
      $default = $new_value;
    }

    return $default;
  }

  public function create_filter_betheme_disable_footer($default) {
    $new_value = $this->options['disable_footer_copy']['value'];

    if($new_value){
      $default = $new_value;
    }

    return $default;
  }


  public function __construct() {
    parent::__construct();

    $this->built_in_features['disable_theme_version']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/betheme-version.png';
    $this->built_in_features['disable_support_link']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/disable-manual-and-support-tab.png';
    $this->built_in_features['disable_changelog_link']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/disable-changelog-tab.png';
    $this->built_in_features['disable_theme_update']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/disable-update-button.png';
    $this->built_in_features['disable_advanced_tab']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/disable-advanced-tab.png';
    $this->built_in_features['disable_hooks_tab']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/disable-hooks-tab.png';
    $this->built_in_features['disable_footer_copy']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/disable-footer-copyright.png';

    add_action( 'admin_menu', array( $this, 'add_menu'));

    //values, iterated to check if there is no new attributes
    //some of them, are cached in database
    $this->options = $this->iterate_merge_array(self::page_name);

    //values straight from the php schema
    $this->get_attributes = $this->get_page_attributes(self::page_name);

    if(!WHITE_LABEL){
      //Update theme functionality disable
      $this->theme_name = get_stylesheet();
      add_filter( 'site_transient_update_themes', array( $this, 'disable_theme_update_notification' ) );

      //Filters
      add_action( 'load_textdomain', array($this, 'create_filters_loop'), 1);
    }
  }
}

new Be_custom_built_in_features();
