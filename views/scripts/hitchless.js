jQuery(function(){             
	var panel = window.location.hash
	$(panel).show();
	$('#showcinfo').click(function(e){
		$('#clientinfo').toggle();
		e.preventDefault();
	});
	$('.clientmenu').click(function(e){
		$('#clientnav').toggle();
		e.preventDefault();
	});
	$('#servicemenu').click(function(e){
		$('#addservice').toggle();
		e.preventDefault();
	});
	$('#nav a').click(function(e){
		targetdiv = $(this).attr('href');
		$("#nav a").removeClass("active");
		$(this).addClass('active');
		$(".panel").hide();
		$(targetdiv).show();
	});
    $(".invoiceproject").click(function(e){
    	$("#newinvoice").show();
    });
	$('.show').click(function(e){
		targetdiv = $(this).attr('href');
		$(targetdiv).toggle();
		$(targetdiv).child("input").focus();
		e.preventDefault();
	});
	$(".filterinvoices").click(function(e){
		target = $(this).attr('href');
		go = target.split("#");
		$(".invoice").hide();
		goclass = "." + go[1];
		$(goclass).show();
		e.preventDefault();
	});
	$(".showallinvoices").click(function(e){
		$(".invoice").show();
		e.preventDefault();
	});

	$('.sheet').click(function(e){
		foo = $(this).attr("href");
		$(this).next(".sheetplaceholder").load(foo); 
		e.preventDefault();
	});


/*
	$('#timetrack').submit(function(){
		
		bar = $("#pid").val()
		foo = $(this).attr("action");
		
		foobar = foo + "?pid=" + bar
		
		alert(foobar);

		$("#timepost").load(foo); 
 		return false;

	});
*/

});