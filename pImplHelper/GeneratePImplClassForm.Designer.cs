namespace Company.pImplHelper
{
    partial class GeneratePImplClassForm
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.classNameTextbox = new System.Windows.Forms.TextBox();
            this.label1 = new System.Windows.Forms.Label();
            this.OKButton = new System.Windows.Forms.Button();
            this.CancelButton = new System.Windows.Forms.Button();
            this.headerTextbox = new System.Windows.Forms.TextBox();
            this.cppTextbox = new System.Windows.Forms.TextBox();
            this.label2 = new System.Windows.Forms.Label();
            this.label3 = new System.Windows.Forms.Label();
            this.SuspendLayout();
            // 
            // classNameTextbox
            // 
            this.classNameTextbox.Location = new System.Drawing.Point(107, 23);
            this.classNameTextbox.Name = "classNameTextbox";
            this.classNameTextbox.Size = new System.Drawing.Size(454, 19);
            this.classNameTextbox.TabIndex = 0;
            this.classNameTextbox.Text = "NewClass";
            this.classNameTextbox.TextChanged += new System.EventHandler(this.textBox1_TextChanged);
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(13, 26);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(65, 12);
            this.label1.TabIndex = 1;
            this.label1.Text = "Class name";
            // 
            // OKButton
            // 
            this.OKButton.Location = new System.Drawing.Point(405, 139);
            this.OKButton.Name = "OKButton";
            this.OKButton.Size = new System.Drawing.Size(75, 23);
            this.OKButton.TabIndex = 3;
            this.OKButton.Text = "OK";
            this.OKButton.UseVisualStyleBackColor = true;
            this.OKButton.Click += new System.EventHandler(this.OKButton_Click);
            // 
            // CancelButton
            // 
            this.CancelButton.Location = new System.Drawing.Point(486, 140);
            this.CancelButton.Name = "CancelButton";
            this.CancelButton.Size = new System.Drawing.Size(75, 23);
            this.CancelButton.TabIndex = 4;
            this.CancelButton.Text = "Cancel";
            this.CancelButton.UseVisualStyleBackColor = true;
            this.CancelButton.Click += new System.EventHandler(this.CancelButton_Click);
            // 
            // headerTextbox
            // 
            this.headerTextbox.Location = new System.Drawing.Point(12, 69);
            this.headerTextbox.Name = "headerTextbox";
            this.headerTextbox.Size = new System.Drawing.Size(549, 19);
            this.headerTextbox.TabIndex = 6;
            // 
            // cppTextbox
            // 
            this.cppTextbox.Location = new System.Drawing.Point(12, 110);
            this.cppTextbox.Name = "cppTextbox";
            this.cppTextbox.Size = new System.Drawing.Size(549, 19);
            this.cppTextbox.TabIndex = 7;
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(12, 54);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(120, 12);
            this.label2.TabIndex = 8;
            this.label2.Text = "Path of header file (.h)";
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(13, 95);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(116, 12);
            this.label3.TabIndex = 9;
            this.label3.Text = "Path of cpp file (.cpp)";
            // 
            // GeneratePImplClassForm
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 12F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(577, 174);
            this.Controls.Add(this.label3);
            this.Controls.Add(this.label2);
            this.Controls.Add(this.cppTextbox);
            this.Controls.Add(this.headerTextbox);
            this.Controls.Add(this.CancelButton);
            this.Controls.Add(this.OKButton);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.classNameTextbox);
            this.Name = "GeneratePImplClassForm";
            this.Text = "Generate a class in pImpl idiom";
            this.FormClosed += new System.Windows.Forms.FormClosedEventHandler(this.GeneratePImplClassForm_FormClosed);
            this.Load += new System.EventHandler(this.GeneratePImplClassForm_Load);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.TextBox classNameTextbox;
        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Button OKButton;
        private System.Windows.Forms.Button CancelButton;
        private System.Windows.Forms.TextBox headerTextbox;
        private System.Windows.Forms.TextBox cppTextbox;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.Label label3;
    }
}