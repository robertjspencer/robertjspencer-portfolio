(function($) {

	var	$window = $(window),
		$body = $('body'),
		$main = $('#main');

	var themeStorageKey = 'preferred-theme',
		root = document.documentElement,
		$themeToggle = $('#theme-toggle');

	function getStoredTheme() {
		try {
			return window.localStorage.getItem(themeStorageKey);
		}
		catch (error) {
			return null;
		}
	}

	function setStoredTheme(theme) {
		try {
			window.localStorage.setItem(themeStorageKey, theme);
		}
		catch (error) {}
	}

	function getActiveTheme() {
		return root.getAttribute('data-theme') || 'light';
	}

	function applyTheme(theme) {
		var nextLabel = theme === 'dark' ? 'Light mode' : 'Dark mode';

		root.setAttribute('data-theme', theme);
		root.style.colorScheme = theme;

		if ($themeToggle.length > 0) {
			$themeToggle.attr('aria-pressed', theme === 'dark' ? 'true' : 'false');
			$themeToggle.attr('title', nextLabel);
			$themeToggle.find('.theme-toggle-label').text(nextLabel);
		}
	}

	// Breakpoints.
		breakpoints({
			xlarge:   [ '1281px',  '1680px' ],
			large:    [ '981px',   '1280px' ],
			medium:   [ '737px',   '980px'  ],
			small:    [ '481px',   '736px'  ],
			xsmall:   [ '361px',   '480px'  ],
			xxsmall:  [ null,      '360px'  ]
		});

	// Play initial animations on page load.
		$window.on('load', function() {
			window.setTimeout(function() {
				$body.removeClass('is-preload');
			}, 100);
		});

	if ($themeToggle.length > 0) {
		applyTheme(getActiveTheme());

		$themeToggle.on('click', function() {
			var nextTheme = getActiveTheme() === 'dark' ? 'light' : 'dark';

			applyTheme(nextTheme);
			setStoredTheme(nextTheme);
		});
	}

	if (window.matchMedia) {
		var themeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)'),
			handleThemeMediaChange = function(event) {
				if (getStoredTheme())
					return;

				applyTheme(event.matches ? 'dark' : 'light');
			};

		if (themeMediaQuery.addEventListener)
			themeMediaQuery.addEventListener('change', handleThemeMediaChange);
		else if (themeMediaQuery.addListener)
			themeMediaQuery.addListener(handleThemeMediaChange);
	}

	// Nav.
		var $nav = $('#nav');
		var $mobileNavToggle = $('#mobile-nav-toggle');

		if ($nav.length > 0) {
			var mobileNavQuery = window.matchMedia ? window.matchMedia('(max-width: 736px)') : null;
			var setMobileNavState = function(isOpen) {
				$nav.toggleClass('is-open', isOpen);
				if ($mobileNavToggle.length > 0)
					$mobileNavToggle.attr('aria-expanded', isOpen ? 'true' : 'false');
			};
			var syncMobileNavForViewport = function() {
				if (!mobileNavQuery || !mobileNavQuery.matches)
					setMobileNavState(false);
			};

			if ($mobileNavToggle.length > 0) {
				$mobileNavToggle.on('click', function() {
					setMobileNavState(!$nav.hasClass('is-open'));
				});

				$window.on('resize', syncMobileNavForViewport);
				syncMobileNavForViewport();
			}

			// Shrink effect.
				$main
					.scrollex({
						mode: 'top',
						enter: function() {
							$nav.addClass('alt');
						},
						leave: function() {
							$nav.removeClass('alt');
						},
					});

			// Links.
				var $nav_a = $nav.find('a');

				$nav_a
					.scrolly({
						speed: 1000,
						offset: function() { return $nav.height(); }
					})
					.on('click', function() {

						var $this = $(this);

						// External link? Bail.
							if ($this.attr('href').charAt(0) != '#')
								return;

						// Deactivate all links.
							$nav_a
								.removeClass('active')
								.removeClass('active-locked');

						// Activate link *and* lock it (so Scrollex doesn't try to activate other links as we're scrolling to this one's section).
							$this
								.addClass('active')
								.addClass('active-locked');

						// Collapse mobile nav after selecting a section link.
							if ($nav.hasClass('is-open'))
								setMobileNavState(false);

					})
					.each(function() {

						var	$this = $(this),
							id = $this.attr('href'),
							$section = $(id);

						// No section for this link? Bail.
							if ($section.length < 1)
								return;

						// Scrollex.
							$section.scrollex({
								mode: 'middle',
								initialize: function() {

									// Deactivate section.
										if (browser.canUse('transition'))
											$section.addClass('inactive');

								},
								enter: function() {

									// Activate section.
										$section.removeClass('inactive');

									// No locked links? Deactivate all links and activate this section's one.
										if ($nav_a.filter('.active-locked').length == 0) {

											$nav_a.removeClass('active');
											$this.addClass('active');

										}

									// Otherwise, if this section's link is the one that's locked, unlock it.
										else if ($this.hasClass('active-locked'))
											$this.removeClass('active-locked');

								}
							});

					});

		}

	// Scrolly.
		$('.scrolly').scrolly({
			speed: 1000
		});

})(jQuery);