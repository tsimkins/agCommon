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
            
            var main_list = jq("<div class='rmm-main-list'></div>");
            
            jq(this).children().appendTo(main_list);    // mark main menu list
            
            jq(this).append(main_list);
            
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

            var $menucontrols ="<div class='rmm-toggled-controls'>" + menubutton + "<h2 class='rmm-toggled-title'>" + menutitle + "</h2></div>";

            jq(this).prepend("<div class='rmm-toggled rmm-closed'>"+$menucontrols+"</div>")
            jq(this).children('.rmm-toggled').append($menulist);

        }
    );
}

jq(document).ready(function() {

    // dynamically add .rmm class
    jq('#portal-searchbox').addClass('rmm');
    jq('#document-toc').addClass('rmm');
    
    // Add 'rmm-multi-menu' class to portal-header.  This allows only one open
    // menu per multi-menu object.
    
    jq('#portal-header').addClass('rmm-multi-menu');
    
    // Move the 'main' navigation items into one menu area
    var mobile_nav = jq('<div id="mobile-navigation" class="rmm"></div>');
    
    // Add the left and top nav to the menu.  
    // Show the left nav before the top nav
    jq('body:not(.navigation-mobile) #portal-column-one .portlet-mobile-navigation').addClass('rmm-main').clone().removeClass('rmm-main').appendTo(mobile_nav)  

    jq('.top-navigation').addClass('rmm-main').clone().removeClass('rmm-main').appendTo(mobile_nav)   

    
    mobile_nav.find('.left-column-navigation .hiddenStructure, .top-navigation .hiddenStructure').each(
        function() {
            jq(this).removeClass('hiddenStructure');
        }
    );
    
    // Remove duplicate portletwrapper ids
    mobile_nav.find(".portletWrapper").each(
        function () {
            jq(this).removeAttr('id');
        }
    );
    
    if (mobile_nav.children().size()) {
        mobile_nav.appendTo('#portal-header');
    }

    responsiveMobileMenu();
    
    /* slide down mobile menu on click */
    
    jq('.rmm-toggled').click(function(){
                
        if ( jq(this).is(".rmm-closed")) {

            /* Close all open menus before opening a new one */

            jq(this).parents('.rmm-multi-menu').each(
                function () {
                    jq(this).find('.rmm-toggled').addClass('rmm-closed');
                }
            );

            jq(this).removeClass("rmm-closed");
        }
        else {
            jq(this).addClass("rmm-closed");
        }
        
    });    


    /* 
        Prevent clicks inside menu from toggling menu 
        
        https://api.jquery.com/event.stoppropagation/
    */    
    jq('.rmm-toggled .rmm-main-list').click(function(event){
        event.stopPropagation();
    });   

});