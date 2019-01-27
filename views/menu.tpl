<html lang="en">
    <head>
        <!DOCTYPE html>
		<link href="{{base_url}}static/noty/noty.css" rel="stylesheet">
		<script src="{{base_url}}static/noty/noty.min.js" type="text/javascript"></script>
		<style>
            #divmenu {
				background-color: #000000;
				padding-top: 2em;
				padding-bottom: 1em;
				padding-left: 1em;
				padding-right: 128px;
			}
			.prompt {
				background-color: #333333 !important;
				color: white !important;
				border-radius: 3px !important;
			}
			.searchicon {
				color: white !important;
			}
        </style>
    </head>
    <body>
		% from get_argv import config_dir

		% import os
		% import sqlite3
        % from config import settings

        %if settings.sonarr.getboolean('only_monitored'):
        %    monitored_only_query_string_sonarr = ' AND monitored = "True"'
        %else:
        %    monitored_only_query_string_sonarr = ""
        %end

        %if settings.radarr.getboolean('only_monitored'):
        %    monitored_only_query_string_radarr = ' AND monitored = "True"'
        %else:
        %    monitored_only_query_string_radarr = ""
        %end

        % conn = sqlite3.connect(os.path.join(config_dir, 'db', 'bazarr.db'), timeout=30)
    	% c = conn.cursor()
		% wanted_series = c.execute("SELECT COUNT(*) FROM table_episodes WHERE missing_subtitles != '[]'" + monitored_only_query_string_sonarr).fetchone()
		% wanted_movies = c.execute("SELECT COUNT(*) FROM table_movies WHERE missing_subtitles != '[]'" + monitored_only_query_string_radarr).fetchone()

		<div id="divmenu" class="ui container">
			<div class="ui grid">
				<div class="middle aligned row">
					<div class="three wide column">
						<a href="{{base_url}}"><img class="logo" src="{{base_url}}static/logo128.png"></a>
					</div>

					<div class="twelve wide column">
						<div class="ui grid">
								<div class="row">
								<div class="sixteen wide column">
									<div class="ui inverted borderless labeled icon massive menu seven item">
										<div class="ui container">
											% if settings.general.getboolean('use_sonarr'):
											<a class="item" href="{{base_url}}series">
												<i class="play icon"></i>
												Series
											</a>
                                            % end
											% if settings.general.getboolean('use_radarr'):
											<a class="item" href="{{base_url}}movies">
												<i class="film icon"></i>
												Movies
											</a>
                                            % end
											<a class="item" href="{{base_url}}history">
												<i class="wait icon"></i>
												History
											</a>
											<a class="item" href="{{base_url}}wanted">
												<i class="warning sign icon">
													% if settings.general.getboolean('use_sonarr'):
													<div class="floating ui tiny yellow label" style="left:90% !important;top:0.5em !important;">
														{{wanted_series[0]}}
													</div>
													% end
													% if settings.general.getboolean('use_radarr'):
													<div class="floating ui tiny green label" style="left:90% !important;top:3em !important;">
														{{wanted_movies[0]}}
													</div>
													% end
												</i>
												Wanted
											</a>
											<a class="item" href="{{base_url}}settings">
												<i class="settings icon"></i>
												Settings
											</a>
											<a class="item" href="{{base_url}}system">
												<i class="laptop icon"></i>
												System
											</a>
											<a id="donate" class="item" href="https://beerpay.io/morpheus65535/bazarr">
												<i class="red heart icon"></i>
												Donate
											</a>
										</div>
									</div>
								</div>
							</div>

							<div style='padding-top:0;' class="row">
								<div class="three wide column"></div>

								<div class="ten wide column">
									<div class="ui search">
										<div class="ui left icon fluid input">
											<input class="prompt" type="text" placeholder="Search in your library">
											<i class="searchicon search icon"></i>
										</div>
									</div>
								</div>

								<div class="three wide column"></div>
							</div>
						</div>
                    </div>
                </div>
            </div>

			% restart_required = c.execute("SELECT configured, updated FROM system").fetchone()
			% c.close()

			% if restart_required[1] == '1' and restart_required[0] == '1':
			    <div class='ui center aligned grid'><div class='fifteen wide column'><div class="ui red message">Bazarr need to be restarted to apply last update and changes to general settings. Click <a href=# id="restart_link">here</a> to restart.</div></div></div>
			% elif restart_required[1] == '1':
				<div class='ui center aligned grid'><div class='fifteen wide column'><div class="ui red message">Bazarr need to be restarted to apply last update. Click <a href=# id="restart_link">here</a> to restart.</div></div></div>
			% elif restart_required[0] == '1':
				<div class='ui center aligned grid'><div class='fifteen wide column'><div class="ui red message">Bazarr need to be restarted to apply changes to general settings. Click <a href=# id="restart_link">here</a> to restart.</div></div></div>
			% end
            <div class="container">
            % import bazarr
            % if bazarr.UPDATE_AVAILABLE is None:
                <div id="updatebar" class='ui center aligned grid'><div class='fifteen wide column'><div class="ui red message">
                    You are running an unknown version of Bazarr.
                    <a href="update">Update</a>
                </div></div></div>
            % elif bazarr.UPDATE_AVAILABLE == 'release':
                <div id="updatebar" class='ui center aligned grid'><div class='fifteen wide column'><div class="ui red message">
                    A <a href="{{'https://github.com/morpheus65535/bazarr/releases/tag/%s' % bazarr.LATEST_RELEASE}}" target="_blank">
                    new release ({{bazarr.LATEST_RELEASE}})</a> of Bazarr is available!
                    <a href="update">Update</a>
                </div></div></div>
            % elif bazarr.UPDATE_AVAILABLE == 'commit':
                <div id="updatebar" class='ui center aligned grid'><div class='fifteen wide column'><div class="ui red message">
                    A <a href="{{'https://github.com/morpheus65535/bazarr/compare/%s...%s' % (bazarr.CURRENT_VERSION, bazarr.LATEST_VERSION)}}" target="_blank">
                    newer version</a> of Bazarr is available!<br />
                    You are {{bazarr.COMMITS_BEHIND}} commit{{'s' if bazarr.COMMITS_BEHIND > 1 else ''}} behind.
                    <a href="update">Update</a>
                </div></div></div>
            % end
		</div>
    </body>
</html>

<script>
    $('.ui.search')
        .search({
            apiSettings: {
                url: '{{base_url}}search_json/{query}',
                onResponse: function(results) {
                    const response = {
                        results : []
                    };
                    $.each(results.items, function(index, item) {
                        response.results.push({
                            title       : item.name,
                            url         : item.url
                        });
                    });
                    return response;
                }
            },
            minCharacters : 2
        })
    ;

    if (window.location.href.indexOf("episodes") > -1) {
    	$('.menu').css('background', '#000000');
    	$('.menu').css('opacity', '0.8');
    	$('#divmenu').css('background', '#000000');
    	$('#divmenu').css('opacity', '0.8');
    	$('#divmenu').css('box-shadow', '0 0 5px 5px #000000');
    }
    else if (window.location.href.indexOf("movie/") > -1) {
    	$('.menu').css('background', '#000000');
    	$('.menu').css('opacity', '0.8');
    	$('#divmenu').css('background', '#000000');
    	$('#divmenu').css('opacity', '0.8');
    	$('#divmenu').css('box-shadow', '0 0 5px 5px #000000');
    }
    else {
    	$('.menu').css('background', '#272727');
    	$('#divmenu').css('background', '#272727');
    }

    $('#restart_link').on('click', function(){
		$('#loader_text').text("Bazarr is restarting, please wait...");
		$.ajax({
			url: "{{base_url}}restart",
			async: true
		})
		.done(function(){
    		setTimeout(function(){ setInterval(ping, 2000); },8000);
		});
	});

	% from config import settings
	% ip = settings.general.ip
	% port = settings.general.port
	% base_url = settings.general.base_url

	if ("{{ip}}" === "0.0.0.0") {
		public_ip = window.location.hostname;
	} else {
		public_ip = "{{ip}}";
	}

	protocol = window.location.protocol;

	if (window.location.port === '{{current_port}}') {
	    public_port = '{{port}}';
    } else {
        public_port = window.location.port;
    }

	function ping() {
		$.ajax({
			url: protocol + '//' + public_ip + ':' + public_port + '{{base_url}}',
			success: function(result) {
				window.location.href= protocol + '//' + public_ip + ':' + public_port + '{{base_url}}';
			}
		});
	}
</script>

<script type="text/javascript">
	if (location.protocol != 'https:')
	{
		var ws = new WebSocket("ws://" + window.location.host + "{{base_url}}websocket");
	} else {
		var ws = new WebSocket("wss://" + window.location.host + "{{base_url}}websocket");
	}

    ws.onmessage = function (evt) {
        new Noty({
			text: evt.data,
			timeout: 3000,
			progressBar: false,
			animation: {
				open: null,
				close: null
			},
			killer: true,
    		type: 'info',
			layout: 'bottomRight',
			theme: 'semanticui'
		}).show();
    };
</script>