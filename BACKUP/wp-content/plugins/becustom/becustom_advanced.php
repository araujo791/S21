<?php
class Be_custom_advanced extends Be_custom {
  const page_name = 'advanced';

  public $options = array();

  public $action_name = '';

  public $notices = array(
		'no_purchase_code' => 'Please enter purchase code.',
		'code_format' => 'Invalid purchase code format.',
		'no_connection' => 'Could not connect to the Envato (ThemeForest) server to verify purchase. Please try again later.',

		'registered' => 'Thank you for registration.',
		'deregistered' => 'Theme deregistered.',
	);

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

  public function export_options() {
    $subpages = $this->becustom_subpages;
    $options_saved = array();

    foreach ($subpages as $page) {
      $options_saved[] = array(
        'title' => $page,
        'options' => get_option('be_custom_'.$page)
      );
    }

    return base64_encode( json_encode($options_saved) );
  }

  public function import_options() {
    if($_POST && $_POST['action_name'] === 'import'){
      $subpages = $this->becustom_subpages;
      $base64_decoded = base64_decode( $_POST['import-content'] );
      $json_decoded = json_decode($base64_decoded, true);
      $page_count = 0; //0 = branding, 1 = built_in_features, etc...

      //if it's not array, then code for import is wrong!
      if(is_array($json_decoded)){
        foreach ($subpages as $page) {
          $options_saved[] = update_option('be_custom_'.$json_decoded[$page_count]['title'], $json_decoded[$page_count]['options']);
          $page_count++;
        }

        echo "<div class='becustom-import-success'> Settings has been imported successfully!  </div>";
      } else {
        echo "<div class='becustom-import-error'> Oh no! Something went wrong.  </div>";
      }
    }
  }

  public function deregister()
	{
    if($_POST && $_POST['action_name'] === 'deregister'){
      delete_site_option('envato_purchase_code_7758048');

      $location = get_home_url().'/wp-admin/admin.php?page=betheme';
      wp_safe_redirect($location);
    }
	}

  public function __construct() {
    parent::__construct();
    add_action( 'admin_menu', array( $this, 'add_menu'));

    //values, iterated to check if there is no new attributes
    //some of them, are cached in database
    $this->options = $this->iterate_merge_array(self::page_name);

    //values straight from the php schema
    $this->get_attributes = $this->get_page_attributes(self::page_name);
  }
}

new Be_custom_advanced();
