$(document).ready(function(){

/*
	var panel = window.location.hash;
	if (!panel) panel = '#projects';
	var show = '#tab a[href="'+panel+'"]';
	$(show).tab('show');
*/
/*
	$('.shown').click(function(){
		e.preventDefault();
		foo = $(this).attr("href");

		$(foo).toggle();

	});
*/




	// attach the plugin to an element
	$('#timelist li').swipeDelete({
		btnTheme: 'b',
		btnLabel: 'Delete',
		btnClass: 'aSwipeButton',
		click: function(e){
			e.preventDefault();
			var url = $(e.target).attr('href');
			$(this).parents('li').slideUp();
			$.post(url, function(data) {
				console.log(data);

			});
		}
	});


    

});