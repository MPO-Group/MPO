<?php
#MPO CERTIFICATE REQUEST FORM

//Set no caching
header("Expires: Mon, 26 Jul 1997 05:00:00 GMT");
header("Last-Modified: " . gmdate("D, d M Y H:i:s") . " GMT");
header("Cache-Control: no-store, no-cache, must-revalidate");
header("Cache-Control: post-check=0, pre-check=0", false);
header("Pragma: no-cache");

//mpo cert request goes to:
$to="jas@psfc.mit.edu"; 
$sub="MPO Certificate Request";
$headers = 'From: mpo@fusion.gat.com' . "\r\n";

//error message for user
$msg="";

//process form
if(!empty($_POST['s'])) {
	$comment="";
	if(!empty($_POST['fname']))
		$fname=sanitize_str($_POST['fname']);
	else
		$msg.="Please enter your first name.<br/>";
		
	if(!empty($_POST['lname']))
		$lname=sanitize_str($_POST['lname']);
	else
		$msg.="Please enter your last name.<br/>";

	if(!empty($_POST['inst']))
		$inst=sanitize_str($_POST['inst']);
	else
		$msg.="Please enter your institution.<br/>";

	if(!empty($_POST['email'])) {
		if(valid_email($_POST['email']))
			$email=$_POST['email'];
		else
			$msg.="Please enter a valid email.<br/>";
	}
	else
		$msg.="Please enter a valid email.<br/>";

	if(!empty($_POST['mpo_contact']))
		$mpo_contact=sanitize_str($_POST['mpo_contact']);
	else
		$msg.="Please enter your MPO contact.<br/>";

	if(!empty($_POST['tele']))
		$tele=sanitize_str($_POST['tele']);
	else
		$msg.="Please enter your phone number.<br/>";		

	if(!empty($_POST['comment']))
		$comment=sanitize_str($_POST['comment']);

	#if no errors send email
	if($msg=="") {
	
$body = <<<EOT
MPO Certificate request from:

Name: $fname $lname

Institution: $inst
Email: $email
Telephone: $tele
MPO Contact: $mpo_contact
Comments: $comment

EOT;

	mail($to,$sub,$body,$headers);
	$msg="Thank you! Your request has been submitted and will be processed shortly.";
	}
}

//validate user input
function sanitize_str($str) {
	return filter_var(htmlspecialchars($str), FILTER_SANITIZE_STRING);
}

function valid_email($eml) {
	return filter_var($eml, FILTER_VALIDATE_EMAIL);
}

?>
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>MPO Registration</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Prototype Implementation of MPO Project">
    <meta name="author" content="">
    <!-- Le styles -->
    <link href="assets/bootstrap/css/bootstrap.css" rel="stylesheet">
    <link href="assets/bootstrap/css/bootstrap-responsive.css" rel="stylesheet">
    <link href="assets/css/main.css" rel="stylesheet">
    <!-- Le HTML5 shim, for IE6-8 support of HTML5 elements -->
    <!--[if lt IE 9]>
      <script src="//html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->
    <script src="assets/bootstrap/js/jquery.js"></script>
    <script src="assets/js/jquery-ui.min.js"></script>
  </head>

  <body>
    <div class="navbar navbar-fixed-top">
      <div class="navbar-inner">
        <div class="container-fluid">
          <button type="button" class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="brand">&nbsp;&nbsp;</a>
          <div class="nav-collapse collapse">
            <ul class="nav">
                <li><a href="index.html#about" class="anchorLink"><span class="icon-search"></span> About</a></li>
                <li><a href="index.html#team" class="anchorLink"><span class="icon-user"></span> Team</a></li>
                <li><a href="index.html#users" class="anchorLink"><span class="icon-globe"></span> Users &amp; Institutions</a></li>
                <li><a href="index.html#demo" class="anchorLink"><span class="icon-play"></span> Try MPO</a></li>
                <li><a href="index.html#register" class="anchorLink"><span class="icon-check"></span> Become a User</a></li>
                <li><a href="index.html#pubs" class="anchorLink"><span class="icon-book"></span> Publications</a></li>
                <li><a href="https://mpo.psfc.mit.edu/mpo/doc/" target="_blank"><span class="icon-list"></span> Documentation</a></li>
                <li><a href="mailto: mpo-info@fusion.gat.com" target="_blank"><span class="icon-envelope"></span> Contact</a></li>
            </ul>
          </div><!--/.nav-collapse -->
        </div><!--/.container-fluid-->
      </div><!--./navbar-inner-->
    </div><!--./navbar-->
      
    <div class="container-fluid">
      <div class="leaderboard">
      	<div class="row-fluid">        		
        	<div class="span12">
        	<h1>Documenting Scientific Workflows</h1>
            <h3>The Metadata, Provenance, and Ontology Project</h3>
       		<hr/>
            
            <p style="padding-top: 20px;" id="about">
            <font class="big">Become a MPO user</font><br>
			</p>
            
            <p>Accessing MPO requires a MPO registered certificate from one of our supported certificate authorities:
            <ul>
            <li>MIT</li>
            <li>Open Science Grid</li>
            </ul>
            </p>
            <hr />
            <p style="padding-top: 20px;">
            <span class="icon-ok"></span> If you already <strong>have</strong> a certificate generated from a certificate authority listed above...<br/ ><font color=success><strong>You can use your existing certificate to register and access the MPO systems.</strong></font> <br /><a href="users.html">Click here to select from a list of current MPO production systems</a> or go directly to the MPO system you wish to access, select your existing certificate when prompted for a User Identification Request (Certificate) and you will be asked to register with the selected MPO system.
            </p>
            <hr />
            <p style="padding-top: 20px;">
            <span class="icon-ok"></span> If you <strong>do not have</strong> a certificate generated from a certificate authority listed above OR if you would like to use a MPO-specific certificate...<br /><font color=success><strong>You can apply for a certificate which the MPO team can generate for you.</strong></font><br />Plesae use the form below to submit a request.
            </p>
            
            <p  style="padding-top: 20px;">
            <big>MPO certificate request form</big><br>
            <p class="text-error"><em><small>&nbsp;<?php if($msg != "") echo "<strong>$msg</strong>"; ?></small></em></p>
			</p>
            <form data-toggle="validator" role="form" id="reg_form" class="form-horizontal span12" action="<?php echo htmlspecialchars("register.php#reg_form", ENT_QUOTES, "utf-8"); ?>" method="post"> 
                <div class="control-group">
                    <label class="control-label">*First Name</label>
                    <div class="controls">
                        <input required type="text" id="firstname" name="fname" class="form-control span10" value="<?php if(!empty($fname)) echo $fname; ?>">
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label">*Last Name</label>
                    <div class="controls">
                        <input type="text"  required id="lastname" name="lname" class="form-control span10" value="<?php if(!empty($lname)) echo $lname; ?>">
                    </div>
                </div>     
                <div class="control-group">
                    <label class="control-label">*Organization</label>
                    <div class="controls">
                        <input type="text"  required id="organization" name="inst" class="form-control span10" value="<?php if(!empty($inst)) echo $inst; ?>">
                    </div>
                </div>                              
                 <div class="control-group">
                    <label class="control-label" for="email">*Email</label>
                    <div class="controls">
                        <input type="email"  required id="email" name="email" class="form-control span10" value="<?php if(!empty($email)) echo $email; ?>">
                    </div>
                </div>
                 <div class="control-group">
                    <label class="control-label">*Telephone</label>
                    <div class="controls">
                        <input type="text"  required id="phone" name="tele" class="form-control span10" value="<?php if(!empty($tele)) echo $tele; ?>">
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label">*MPO Contact</label>
                    <div class="controls">
                        <input type="text"  required name="mpo_contact" class="form-control mpo_contact" value="<?php if(!empty($lname)) echo $mpo_contact; ?>">
                    </div>
                </div>
                <div class="control-group">
                    <label class="control-label">Comments</label>
                    <div class="controls">
                        <textarea type="text" name="comment" class="span10"><?php if(!empty($comment)) echo $comment; ?></textarea>
                        <br/><br/>
                         <span class="muted"><small><em>*required fields</em></small></span>
                    </div>
                </div>                                              
                <div class="form-group">
                    <div class="controls">
                        <button type="submit" class="btn btn-success" id="submit">Request a MPO Certificate</button>
                    </div>
                </div>
                <input type="hidden" name="s" value="1">
             </form>
             
            </div><!-- end of span12-->
		</div><!-- end of row-fluid-->
     </div> <!-- end leaderboard -->
      
     <footer>
        <div><span class="pull-left muted">&copy; MPO Team 2015</span></div> 
     </footer>

    </div> <!-- /container-fluid -->
  </body>
</html>

