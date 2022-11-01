window.onload = function () {
    document.getElementById("download")
        .addEventListener("click", () => {
            const invoice = this.document.getElementById("recibo");
            console.log(invoice);
            console.log(window);
            var opt = {
                margin: 0,
                filename: 'comprobante_vivastartup.pdf',
                image: { type: 'jpeg', quality: 0.98 },
		pagebreak:  {avoid: 'tr'},
                html2canvas: { scale: 1 },
                jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
            };
            html2pdf().from(invoice).set(opt).save();
        })
}