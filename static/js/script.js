$('.h-close').click(function() {
    $(this).closest('.h-modal').fadeOut(200);
});

$(document).mouseup(function(e) {
    var container = $(".h-modal-content");
    if (container.has(e.target).length === 0) {
        container.closest('.h-modal').fadeOut(200);
    }
});
$('.modal-btn').click(function() {
    var modalId = $(this).attr('data-modal');
    $(modalId).fadeIn(200);
});
setTimeout(function() {
    $('.condition').hide(600);
}, 2000);

function setcurrency(currency) {
    document.getElementById("currency").value = currency;
    console.log(document.getElementById("currency").value)
}

$('.pay-amount-btn.minus').click(function(){
    var amountVal = $(this).closest('.pay-amount').find('.pay-amount-input input').val();
    if (amountVal > 1) {
        $(this).closest('.pay-amount').find('.pay-amount-input input').val(amountVal - 1);
        document.getElementById("amount").value--;
        document.getElementById("cost").innerHTML = +document.getElementById("cost").innerHTML - +document.getElementById("cost0").innerHTML;
    }
});


function modalOpen() {
    $('#confirmation-modal').fadeIn(200);
}
setTimeout(modalOpen, 100);


$('.slider').slick({
    centerMode: true,
    centerPadding: "33%",
    prevArrow: $('.slider-direction .left-arrow'),
    nextArrow: $('.slider-direction .right-arrow'),
    autoplaySpeed: 200,
    responsive: [{
            breakpoint: 1200,
            settings: {
                centerPadding: '0',
                centerMode: false,
                slidesToShow: 2,
            }
        },
        {
            breakpoint: 768,
            settings: {
                centerPadding: '0',
                centerMode: false,
                slidesToShow: 1,
            },
        }
    ]
});


$('.pay-block').click(function() {
    $(this).closest('.pay-row').find('.pay-block').removeClass('active');
    $(this).addClass('active');
});


$('.change-btn').click(function() {
    var change = $(this).attr('data-change');
    $('.content-item').removeClass('active');
    $(change).addClass('active');
    $('.left-arrow').click();
    $('.loader').fadeIn();
    setTimeout(function() {
        $('.loader').fadeOut();
    }, 1000);
});

$('.content-item-close').click(function() {
    $('.content-item').removeClass('active');
    $('.content-item.first').addClass('active');
});

