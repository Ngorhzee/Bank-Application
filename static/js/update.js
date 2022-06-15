function update(){
    var totalBalance = document.getElementById("totalBalance").innerText;
    var isBalance = 1;
    $.ajax({
        url:"/home",
        type:"GET",
        success:function(response){
            // totalBalance.innerText = response;
            alert("yess")
        },
        error:function(){
            console.log("Error")
        }

    })
}