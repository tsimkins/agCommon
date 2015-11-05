function limelightPlayerCallback(playerId, eventName, data) {                
    
    if (eventName == 'onPlayerLoad' && (LimelightPlayer.getPlayers() == null || LimelightPlayer.getPlayers().length == 0)) {
        LimelightPlayer.registerPlayer(playerId);
    }

    switch (eventName) {
        case 'onPlayerLoad':
            doOnPlayerLoad();
            break;

        case 'onChannelLoad':
            doOnChannelLoad(data);
            break;

        case 'onMediaLoad':
            doOnMediaLoad(data);
            break;

        case 'onPlayStateChanged':
            doOnPlayStateChanged(data);
            break;

        case 'onPlayheadUpdate':
            doOnPlayheadUpdate(data);
            break; 
    }
}

function doOnPlayerLoad() {
    jq('#state').html("paused");
}

function doOnChannelLoad(e) {
    
    // For want of a native printf...
    function pad(n) {
        return (n < 10) ? ("0" + n) : n;
    }

    // Set the channel title, and the default state
    jq('#channelTitle').html(e.title);
    jq('#state').html("paused");

    

    //create a dynamic playlist of media in the channel
    if (e.mediaList && e.mediaList.length > 0) {

        var playlist_box_wrapper = jq('#playlist-box-wrapper');

        var playlist_box = jq('<table id="playlist-box"></table>');
        var playlist_header = jq('<tr><th>Title</th><th>Duration</th><th>Controls</th></tr>');

        playlist_box.append(playlist_header);

        for (var i = 0; i < e.mediaList.length; i++) {

            var media = e.mediaList[i];

            if (media) {
                var minutes = (media.durationInMilliseconds/60000) << 0;
                var seconds = Math.round((media.durationInMilliseconds/1000) % 60);
                var vid_time = (minutes + ':' + pad(seconds));

                // Button: Play
                var play_button = jq('<a class="button play-button"><span>Play</span></a>');
                play_button.attr('data-media-id', media.id);

                play_button.click(
                    function() {
                        var media_id = jq(this).attr('data-media-id');
                        LimelightPlayer.doSetMedia(media_id, false);
                        LimelightPlayer.doPlay();
                    }
                )

                // Button: Resume
                var resume_button = jq('<a class="button resume-button"><span>Resume</span></a>');
                resume_button.click(
                    function() {
                        LimelightPlayer.doPlay();
                    }
                )

                // Button: Pause
                var pause_button = jq('<a class="button pause-button"><span>Pause</span></a>');
                pause_button.click(
                    function() {
                        LimelightPlayer.doPause();
                    }
                )

                // Player buttons             
                var player_buttons = jq('<td class="player-buttons inactive"></td>');
                player_buttons.attr('id', media.id);
                
                // Append the buttons
                player_buttons.append(play_button);
                player_buttons.append(resume_button);
                player_buttons.append(pause_button);                
        
                // Link for video title
                var video_span = jq('<span></span>');
                video_span.html(media.title);

                var video_link = jq('<a class="playlist-item"></a>');
                video_link.attr('data-media-id', media.id);
                video_link.append(video_span);
                
                video_link.click(
                    function() {
                        var media_id = jq(this).attr('data-media-id');
                        LimelightPlayer.doSetMedia(media_id, false);
                        console.log("Media id " + media_id);
                    }
                )

                // Title container for video title, contains video link
                var video_title = jq('<td class="videoTitle"></td>');
                video_title.append(video_link);

                // Video time
                var video_time = jq('<td class="videoTime"></td>');
                video_time.html(vid_time);
        
                // Row for an individual playlist item                                
                var playlist_row = jq('<tr class="playlist-row"></tr>');
                
                // Append three child rows
                playlist_row.append(video_title);
                playlist_row.append(video_time);
                playlist_row.append(player_buttons);                
    
                // Append playlist row to the playlist box.                
                playlist_box.append(playlist_row);

            }
        }
        
        // Create "Previous" and "Next" links
        
        var previous_link = jq('<a class="prev"><span>Previous</span></a>');
        
        previous_link.click(
            function() {
                LimelightPlayer.doPrevious();
            }
        );
        
        var next_link = jq('<a class="next"><span>Next</span></a>');
        
        next_link.click(
            function() {
                LimelightPlayer.doNext();
            }
        );
        
        // Create the media title
        var media_title = jq('<div>Now Playing: <span id="mediaTitle"></span></div>');

        // get the "Now playing" div
        var now_playing = jq('<div id="now-playing"></div>');

        // Append "Previous" and "Next" links and media title to the Now Playing
        now_playing.append(previous_link);
        now_playing.append(media_title);
        now_playing.append(next_link);

        // Append Now Playing to the wrapper
        playlist_box_wrapper.append(now_playing);

        // Append the playlist box to the wrapper
        playlist_box_wrapper.append(playlist_box);

    } 

    LimelightPlayer.doSkipToIndex(0);

}


function doOnMediaLoad(e) {
    var minutes = (e.durationInMilliseconds/60000) << 0;
    var seconds = Math.round((e.durationInMilliseconds/1000) % 60);
    var vid_time = (minutes + ':' + seconds);

    jq('.player-buttons').removeClass('active');
    jq('.player-buttons').addClass('inactive');
    jq('#' + e.id + '').removeClass('inactive');
    jq('#' + e.id + '').addClass('active');
    jq('.player-buttons .play-button').css('display', 'block');
    jq('.player-buttons .pause-button').css('display', 'none');
    jq('.player-buttons .resume-button').css('display', 'none');

    jq('#mediaTitle').html(e.title);
    jq('#minutes').html(minutes);
    jq('#mediaDescription').html(e.description);
    jq('#totalDuration').html(vid_time);
    jq('#testId').html(e.id);

}

function doOnPlayStateChanged(e) {

    var play_state;

    if (e.isBusy) {
            play_state = "buffering";
    } else if (e.isPlaying) {
            play_state = "playing";        
            jq('.player-buttons.inactive .play-button').css('display', 'block');
            jq('.player-buttons.inactive .pause-button').css('display', 'none');
            jq('.player-buttons.inactive .resume-button').css('display', 'none');
            jq('.player-buttons.active .play-button').css('display', 'none');
            jq('.player-buttons.active .pause-button').css('display', 'block');
            jq('.player-buttons.active .resume-button').css('display', 'none');
    } else {
            play_state = "paused";
            jq('.player-buttons.inactive .play-button').css('display', 'block');
            jq('.player-buttons.inactive .pause-button').css('display', 'none');
            jq('.player-buttons.inactive .resume-button').css('display', 'none');
            jq('.player-buttons.active .play-button').css('display', 'none');
            jq('.player-buttons.active .pause-button').css('display', 'none');
            jq('.player-buttons.active .resume-button').css('display', 'block');
    }

    jq('#state').html(play_state);

}

function doOnPlayheadUpdate(e) {
    jq('#timePosition').html(e.positionInMilliseconds);
}
