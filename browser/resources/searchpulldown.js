jQuery(document).ready(function($) {

    var input_searchstring_focus = function() {
        $('ul#search').addClass('show');
        $('input#searchString').unbind('focus.searchstring');  // unbind ourself to avoid looping
        $('ul#search.show li label input:checked').focus(); // allows the user to arrow through the options 
    };

    $('ul#search li label input').keypress(function(event) {
        if (event.keyCode == 13) {  // If 'Enter' is clicked go to the searchbox input and not submit the form
            // Stop the default Enter. IE doesn't understand 'preventDefualt' but does 'returnValue'
            (event.preventDefault) ? event.preventDefault() : event.returnValue = false; 
            focus_to_searchbox();
        }
    });
    $('ul#search li label').keyup(function(event) {
        if (event.keyCode == 32) {  // If the 'space bar' is pressed, go to the searchbox input
            focus_to_searchbox();
        }
    });
    $('body').keydown(function(e) {
        var code = e.keyCode ? e.keyCode : e.which;
        if (code == 27) { // if the ESC key is pressed, close the searchbox
            close_searchbox();
        }
    });

    // initial bind
    $('input#searchString').bind('focus.searchstring', input_searchstring_focus);

    $('input#searchString').click(click_open_search_options);
    
    $('div#portal-searchbox').click(function(e) {
        // keep click events from leaving the searchbox to avoid clicks triggering the close below if the clicks are also in the searchbox
        e.stopPropagation();
    });

    $('html').click(close_searchbox); // allow the user to click anywhere else and close the search selections

    $('ul#menu').removeClass('show'); // prove they can do javascript.. if not let the css option takes over
    
    // FUNCTIONS   
    function clear_searchString() {
        // Clear the box if it has the default 'Search' only. Don't want to erase it if there is already a search term
        var searchValue = $('input#searchString').val();
        if (searchValue == 'Search...') {
            $('input#searchString').val('');
        }  
    }

    function focus_to_searchbox() {
        $('input#searchString').select();
        clear_searchString();
    }
    
    function close_searchbox() {
        $('ul#search').removeClass('show');
        $('ul#search li label input').blur();
        // rebind so the box can re-open
        $('input#searchString').bind('focus.searchstring', input_searchstring_focus);
    }
     
    function click_open_search_options() {
        //$('ul#search').addClass('show');
        clear_searchString()
        $('input#searchString').select();
    }

});