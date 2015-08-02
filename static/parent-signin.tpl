<!doctype html>
<html>
  <head>
    <script src="https://code.jquery.com/jquery-2.1.4.min.js"></script>
  </head>
  <body>
    <h1>Parent Signout Page</h1>
    <h2>Please scan your card</h2>
    <form action="/parent-signin" method="POST" id="form">

      % for s in students:
      <label class="checkbox">
        <input type="checkbox" name="students" value="{{s}}" /> {{s}}
      </label>
      % end
      <input type="text" name="barcode" id="barcode">
    </form>

    <script>
      var num = '';
      $(document).keypress(function(e) {
        switch(e.which) {
          case 48:
          case 49:
          case 50:
          case 51:
          case 52:
          case 53:
          case 54:
          case 55:
          case 56:
          case 57:
            num += (e.which-48);
            $('#barcode').val(num);
            break;

          case 13:
            $('#form').submit();
        }
      })
    </script>
  </body>
</html>

