/*

Responsive Mobile Menu v1.0
Plugin URI: responsivemobilemenu.com

Author: Sergio Vitov
Author URI: http://xmacros.com

License: CC BY 3.0 http://creativecommons.org/licenses/by/3.0/

*/

/*
    Modifications by trs22:

        * Replaced $ with jq for Plone
        * Replaced show/hide with remove/add class of '.hiddenStructure' for accessibility.
        * Removed automagic width CSS
        * Removed adaptMenu function (handling with responsive CSS)
        * Combined getMobileMenu into responsiveMobileMenu function
        * Hard set 'minimal' class
*/

function responsiveMobileMenu() {    
        jq('.rmm').each(function() {
            
            jq(this).children().addClass('rmm-main-list');    // mark main menu list
            
            jq(this).addClass('minimal'); // set minimal class
            
            /* build toggled dropdown menu list */
    
            var menutitle = jq(this).attr("data-menu-title");

            if ( menutitle == "" ) {
                menutitle = "Menu";
            }
            else if ( menutitle == undefined ) {
                menutitle = "Menu";
            }

            var $menulist = jq(this).children().detach();

            var menu_icon = jq(this).attr("data-menu-icon");
            
            if ( menu_icon != "" && menu_icon != undefined) {
                menubutton = "<div class='rmm-button'><img src='" + menu_icon + "' alt='Search' /></div>";
            }
            else {
                menubutton = "<div class='rmm-button'><span>&nbsp;</span><span>&nbsp;</span><span>&nbsp;</span></div>";
            }

            var $menucontrols ="<div class='rmm-toggled-controls'><h2 class='rmm-toggled-title'>" + menutitle + "</h2>" + menubutton + "</div>";

            jq(this).prepend("<div class='rmm-toggled rmm-closed'>"+$menucontrols+"</div>")
            jq(this).children('.rmm-toggled').append($menulist);

        }
    );
}

jq(document).ready(function() {

    // dynamically add .rmm class

    jq('.top-navigation').addClass('rmm-main');
    jq('#portal-column-one .portlet-mobile-navigation').addClass('rmm-main');

    jq('#document-toc').addClass('rmm');
    
    // Move the 'main' navigation items into one menu area
    var mobile_nav = jq('<div id="mobile-navigation" class="rmm"></div>');
    
    jq('.rmm-main').each(
        function() {
            jq(this).clone().removeClass('rmm-main').appendTo(mobile_nav);
        }
    );

    mobile_nav.find('.left-column-navigation .hiddenStructure').each(
        function() {
            jq(this).removeClass('hiddenStructure');
        }
    );
    
    mobile_nav.insertAfter('#portal-header');

    responsiveMobileMenu();
    
    /* slide down mobile menu on click */
    
    jq('.rmm-toggled, .rmm-toggled .rmm-button').click(function(){
         if ( jq(this).is(".rmm-closed")) {
              jq(this).removeClass("rmm-closed");
         }
         else {
              jq(this).addClass("rmm-closed");
         }
        
    });    

});