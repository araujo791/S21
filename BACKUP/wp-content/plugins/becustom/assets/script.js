(function($) {

    /* globals jQuery */

    "use strict";

    /**
     * $(document).ready
     * Specify a function to execute when the DOM is fully loaded.
     */

    $(function($) {
        var becustom_changed_something = false;

        /*
          BeTheme brackets from name removal
          Form handler does not see inputs, when they are bracketed
        */
        var mfnInputLooker = $('.mfn-row').find('input, select');
        $(mfnInputLooker).each(function(){
          if ($(this).prop('name')) {
            var beCustom_replacedNonNumeric = ($(this).prop('name')).replace(/\W/g, '');
            $(this).prop('name', beCustom_replacedNonNumeric);
          }
        })


        /*
          Before unload scripts
        */

        $(window).on('beforeunload', function(){
          if( becustom_changed_something ){
            return "Any changes will be lost";
          }
        });

        $(mfnInputLooker).on('click, keydown', function(){
          becustom_changed_something = true;
        })

        //unusual elements

        $('.mfn-row li, .becustom-dashboard-heading, .becustom-dashboard-content').on('click', function(){
          becustom_changed_something = true;
        })

        $('form').on('submit', function() {
          becustom_changed_something = false;
        });


        /**
          Hover | on Touch | .tooltip, .hover_box
         */

        $('.tooltip, .hover_box')
        .on('touchstart', function() {
          $(this).toggleClass('hover');
        })
        .on('touchend', function() {
          $(this).removeClass('hover');
        });


        /*
          License key deregistration
        */

        $('.form-deregister .confirm.deregister').on('click', 'a', function(e) {
          e.preventDefault();

          $(this).parent().hide()
            .next().fadeIn();
        });

        $('.form-deregister .question').on('click', 'a.cancel', function(e) {
          e.preventDefault();

          $(this).parent().hide()
            .prev().fadeIn();
        });


        /**
         * Popup
        */

        $('.popup-link').click(function(){
          var popup_id = $(this).attr('href');
          $(popup_id).fadeIn(0);

        })

        $('.popup-content').click(function(){
          $('.popup-content').fadeOut(0);
        })


        /**
          Import Export tool
        */

        $('.mfn-button').prop('disabled', false);

        $('.form-export input[name="export"]').click(function(e){
          e.preventDefault();

          var getCodeFromHiddenInput = $('input#export-content').val();
          $('.becustom-import-export').html(getCodeFromHiddenInput);
        })

        $('.form-export input[name="import"]').click(function(e){
          if ($('.becustom-import-export').val() === '') {
            e.preventDefault();
          }

          //insert val to hidden input
          $('input#import-content').val( $('.becustom-import-export').val() );
        })


        /**
         * Add CSS Classes to WP Submit button
         */

        $('.submit input').addClass('mfn-button mfn-button-primary');
    });

  })(jQuery);
