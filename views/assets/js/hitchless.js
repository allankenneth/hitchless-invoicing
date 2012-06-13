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
    $(".invoiceproject").on('click', function(){
    	$("#newinvoice").show();
    });
    
    
	$(".invdetail").popover();
	$(".datedetail").popover();
	$(".notedetail").popover();
	$('#showcinfo').modal({backdrop:'false', show:'false'})
	$('#servicemenu').modal({backdrop:'false', show:'false'});

/*
	$('.sheet').on('click',function(e){
		e.preventDefault();
		foo = $(this).attr("href");
		$(this).next(".sheetplaceholder").load(foo); 
	});
*/

}(window.jQuery);