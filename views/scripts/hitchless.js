jQuery(function(){
	var panel = window.location.hash
	$(panel).show();
	$('#showcinfo').click(function(e){
		$('#clientinfo').slideToggle();
		e.preventDefault();
	});
	$('.clientmenu').click(function(e){
		$('#clientnav').slideToggle();
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
	$('.statuschanger button').hide();
	$('.statuschange').change(function(){
		$(this).parent().parent().submit();
		return false;
	});
	$('.sheet').click(function(e){
		foo = $(this).attr("href");
		$(this).next(".sheetplaceholder").load(foo); 
		e.preventDefault();
	});
	/*
$('#timetrack').submit(function(){
        var projectid = $("#pid").val();
        where = "/timesheet?pid=" + projectid
        $("#timepost").html("Processing &hellip;");
		$.ajax({
            type: "POST",
            url: "/timesheet",
            data: $('#timetrack').serialize(),
            success: function() {
                $('#timepost').load(where);
                $(".invoiceproject").each(function(){
                    var p = $(this).val();
                    if(p == projectid) {
                        $(this).removeAttr('disabled');
                    }
                });
            }
        });
        return false;
    });
*/
});
