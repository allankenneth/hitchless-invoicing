$(document).ready(function(){

/*
	var panel = window.location.hash;
	if (!panel) panel = '#projects';
	var show = '#tab a[href="'+panel+'"]';
	$(show).tab('show');
*/
	$('.shown').click(function(){
/* 		e.preventDefault(); */
		foo = $(this).attr("href");

		$(foo).toggle();

	});

    

});