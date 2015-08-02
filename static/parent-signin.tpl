<!doctype html>
<html>
  <head>
    <script src="https://code.jquery.com/jquery-2.1.4.min.js"></script>
  </head>
  <body>
    <h1>Parent Signin Page</h1>
    <h2>Please scan your card</h2>
    <form action="/parent-signin" method="POST" id="form">
      <select name="students" id="students" multiple>
        % for s in students:
        <option value="{{s}}">{{s}}</option>
        % end
      </select>
    </form>

    <script>
      var num = '';
      $(document).keypress(function(e) {
        switch(e.which) {

          case 13:
            $('#form').submit();
        }
      })
    </script>
  </body>
</html>

