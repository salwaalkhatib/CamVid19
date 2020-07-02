
$(function(){
    $('#sendBtn').bind('click',function(){

        var value = document.getElementById("msg").value
        document.getElementById("msg").value=""
        console.log(value)

        $.getJSON('/send_message', {val:value},

        function(data){

        });

    });
  
});
window.addEventListener("load",function(){
    this.console.log("dwjmkldwhqkdhklqwhdhwjldhqldh")
    var update_loop = setInterval(update,100)
    update()
});






function update()
{
    fetch('/get_messages').then(function(response){
        return response.text();
    }).then(function(text){
        
        var jsonText = JSON.parse(text)
        var messages = "";
        
        for(value of jsonText.messages)
        {
            messages = messages+"<br>"+ value;
            console.log(messages)
        }
        document.getElementById("test").innerHTML = messages;
    });
    
}




