<?php
class Be_custom_wp_login extends Be_custom {
  const page_name = 'wp_login';

  public $options = array();

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
        if($value === '0' || $value === '1'){
          $value = filter_var($value, FILTER_VALIDATE_BOOLEAN);
          $actual_user_schema[$key]['value'] = $value;
        }else{
          $actual_user_schema[$key]['value'] = $value;
        }

        $actual_user_schema[$key]['value'] = $value;
      }

      update_option( 'be_custom_'.self::page_name, $actual_user_schema);

      //reload, display new, insertecd values in inputs
      $this->options = $this->iterate_merge_array(self::page_name);
    } else{
      //
    }
  }

  public function wp_login_custom_css() {
    $custom_style = '';

    $becustom_login_logo = $this->options['custom_wplogin_logo']['value'];
    if( trim($becustom_login_logo)  ) {
      $custom_style .= '.login h1 a{background-image:url('.$becustom_login_logo.'); }';
    }

    $becustom_login_bgcolor = $this->options['custom_background_color']['value'];
    $becustom_login_bgimage = $this->options['custom_background_image']['value'];
    if( trim($becustom_login_bgimage) ) {
      $selected_bg_size = $this->options['custom_background_size']['value'];
      $selected_bg_position = $this->options['custom_background_position']['value'];

      /* Copied from class-mfn-builder-front.php */
      $dividedAttrs = explode(';', $selected_bg_position);
      $readyString = '';

      if( $dividedAttrs[0] ) {
        $readyString .= 'background-repeat:'. $dividedAttrs[0] .';';
      }
      if( $dividedAttrs[1] ) {
        $readyString .= 'background-position:'. $dividedAttrs[1] .';';
      }
      if( $dividedAttrs[2] ) {
        $readyString .= 'background-attachment:'. $dividedAttrs[2];
      }

      $custom_style .= 'body.login { background-image:url('.$becustom_login_bgimage.'); background-size: '.$selected_bg_size.'; '.$readyString.'}';
    }else if( trim($becustom_login_bgcolor) ) {
      $custom_style .= 'body.login { background-color:'.$becustom_login_bgcolor.' }';
    }

    $becustom_font_color = $this->options['custom_font_color']['value'];
    if (trim($becustom_font_color)) {
      $custom_style .= 'body.login a { color: '. $becustom_font_color .' !important}';
    }

    $becustom_login_container_aligment = $becustom_font_color = $this->options['custom_login_container_position']['value'];
    $custom_style .= 'body.login #login { float: '. $becustom_login_container_aligment .' }';

    $becustom_login_container_background = $becustom_font_color = $this->options['custom_login_container_background']['value'];
    if (trim($becustom_login_container_background)) {
      $custom_style .= 'body.login form { background-color: '. $becustom_login_container_background .' }';
    }

    $becustom_login_container_font_color = $this->options['custom_login_container_font_color']['value'];
    if (trim($becustom_login_container_font_color)) {
      $custom_style .= 'body.login form { color: '. $becustom_login_container_font_color .' }';
    }

    $becustom_login_container_input_background = $this->options['custom_login_container_input_background']['value'];
    if (trim($becustom_login_container_input_background)) {
      $custom_style .= 'body.login form input{ background: '. $becustom_login_container_input_background .' !important }';
    }

    $becustom_login_container_input_font_color = $this->options['custom_login_container_input_font_color']['value'];
    if (trim($becustom_login_container_input_font_color)) {
      $custom_style .= 'body.login form input{ color: '. $becustom_login_container_input_font_color .' !important }';
    }

    $becustom_login_forgot_password = $this->options['enable_forgot_password']['value'];
    if (!$becustom_login_forgot_password) {
      $custom_style .= 'body.login #nav{ display: none }';
    }

    $becustom_login_goto_link = $this->options['enable_goto_link']['value'];
    if (!$becustom_login_goto_link) {
      $custom_style .= 'body.login #backtoblog{ display: none }';
    }


    echo '<style>'. $custom_style .'</style>';
  }

  public function __construct() {
    parent::__construct();

    $this->wp_login['custom_wplogin_logo']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/wplogin-logo.png';
    $this->wp_login['custom_background_color']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/wplogin-background-color.png';
    $this->wp_login['custom_font_color']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/wplogin-font-color.png';
    $this->wp_login['custom_background_image']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/wplogin-background-color.png';
    $this->wp_login['custom_login_container_background']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/wplogin-container-background.png';
    $this->wp_login['custom_login_container_font_color']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/wplogin-container-font-color.png';
    $this->wp_login['custom_login_container_input_background']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/wplogin-container-input-background-color.png';
    $this->wp_login['custom_login_container_input_font_color']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/wplogin-container-input-font-color.png';
    $this->wp_login['enable_forgot_password']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/wplogin-lost-password.png';
    $this->wp_login['enable_goto_link']['popup_content']['image'] = plugin_dir_url( __FILE__ ).'assets/images/wplogin-go-to-xyz.png';

    add_action( 'admin_menu', array( $this, 'add_menu'));

    //values, iterated to check if there is no new attributes
    //some of them, are cached in database
    $this->options = $this->iterate_merge_array(self::page_name);

    //values straight from the php schema
    $this->get_attributes = $this->get_page_attributes(self::page_name);

    if(!WHITE_LABEL){
      //custom css for login page
      $becustom_login_page = $this->options['enable_custom_login']['value'];
      if($becustom_login_page){
        add_action('login_head', array($this, 'wp_login_custom_css'));
      }
    }
  }
}

new Be_custom_wp_login();
