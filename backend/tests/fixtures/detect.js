/*if (adblock) {
	jQuery('<a href="https://refpa57118.top/L?tag=s_25190m_1107c_&site=25190&ad=1107&r=user/registration.php" rel="nofollow" target="_blank"><img src="/wp-content/uploads/img/melbet-sidebar.png" border="0" alt="" title="" style="margin-bottom: 5px;"></a>').insertBefore('#top-medium-rectangle .adsbygoogle');
	jQuery('#top-medium-rectangle .adsbygoogle').remove();
	jQuery('.bet-button').append('<a href="http://r.lt28.ru/n5VqR:6760/time" rel="nofollow" target="_blank"><img src="/wp-content/uploads/img/melbet-button.jpg" border="0" alt="" title=""></a>');
	jQuery('#broadcast-megabanner').append('<a href="https://refpa31055.top/L?tag=s_25190m_1107c_&site=25190&ad=1107&r=user/registration.php" rel="nofollow" target="_blank"><img src="/wp-content/uploads/img/melbet-horizontal.png" border="0" alt="" title=""></a>');
	jQuery('#broadcast-megabanner .adsbygoogle').remove();
	jQuery('body').css({
		"background-image": "url('/wp-content/uploads/img/melbet-branding.jpg')",
		"background-position": "top center",
		"background-repeat": "no-repeat",
		"background-attachment": "fixed"
	});
	jQuery('.branding-layout').prepend('<a href="http://r.lt28.ru/n5VqR:6760/brending" target="_blank" rel="nofollow" style="position: fixed; display: block; width: 100%; height: 100%; bottom: 0px; left: 0px; right: 0px; top: 0px; margin: auto; background-color: transparent; cursor: pointer;"></a>');
	jQuery('.branding-layout').css({
		"padding-top": "220px",
		"max-width": "1130px",
		"margin": "auto"
	});
	jQuery("#block-alert").html('<div class="adblock-notification"><div class="notification-content"><img class="icon-warning" src="/wp-content/uploads/img/adblock-icon.png"><div class="notification-message">Уважаемый посетитель! Ресурс PimpleTV.ru существует и развивается только благодаря рекламе. Мы стараемся делать для Вас максимально стабильные и качественные трансляции. Пожалуйста, добавьте наш сайт в список исключений блокировщика рекламы. Спасибо за понимание.</div></div><div class="notification-action"><div class="icon-close"></div></div></div>');
}*/

jQuery(document).ready(function() {
	if (jQuery('img[src*="/img/mars_"]').attr('style') == 'display: none !important;') {
		jQuery('.match-info ~ h3').attr('style', 'display: block !important');
		jQuery('.odds').attr('style', 'display: table !important');
		jQuery('img[src*="/img/melbet"]').attr('style', 'display: inline !important');
		jQuery('.tabs').remove();
		jQuery("#block-alert").html('<div class="adblock-notification"><button class="closeButton" type="button">Закрыть</button><div class="notification-content"><div class="notification-content__icon"></div><div class="notification-content__message">Кажется, вы используете блокировщик рекламы. Вместе с рекламой он может отключать и другие важные элементы. Добавьте PimpleTV.ru в исключения, и всё будет в порядке.</div><a class="notification-content__button" rel="nofollow" target="_blank" href="https://yandex.ru/support/common/troubleshooting/yandex-in-adblock.html">Как это сделать</a></div></div>');
	}
	jQuery('.adblock-notification button').click(function() {
		jQuery('.adblock-notification').remove();
	});
});