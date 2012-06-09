!function ($) {

/*
	var panel = window.location.hash;
	if (!panel) panel = '#projects';
	var show = '#tab a[href="'+panel+'"]';
	$(show).tab('show');
*/
	$('.showtime').on('click', function(e){
		e.preventDefault();
		foo = $(this).attr("href");
		$(foo).toggle();
	});
	$(".invdetail").popover();
	$('#showcinfo').modal({backdrop:'false', show:'false'})
	$('#servicemenu').modal({backdrop:'false', show:'false'});
    $(".invoiceproject").on('click', function(){
    	$("#newinvoice").show();
    });
	$('.sheet').on('click',function(e){
		e.preventDefault();
		foo = $(this).attr("href");
		$(this).next(".sheetplaceholder").load(foo); 
	});

}(window.jQuery);